import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import Base, get_db
from src.model import userModel
from src.repository import userRepository
from tests import test_auth

# Criação do banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestUser:

    @pytest.fixture(scope="function", autouse=True)
    def setup(self):
        # Limpa o banco de dados antes de cada teste
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        # Criação de usuários para teste
        self.db = TestingSessionLocal()
        self.user1 = userRepository.create_user(self.db, name="Admin User", connection="ADMIN", email="admin@unb.br", password="123456", activation_code=None)
        self.user2 = userRepository.create_user(self.db, name="Regular User", connection="ALUNO", email="user@unb.br", password="123456", activation_code=None)
        self.user3 = userRepository.create_user(self.db, name="Another User", connection="PROFESSOR", email="another@unb.br", password="123456", activation_code=None)
        self.db.commit()

    def test_get_all_users(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.get("/api/auth/users", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        assert len(data) == 3
        assert data[0]['email'] == "admin@unb.br"
        assert data[1]['email'] == "user@unb.br"
        assert data[2]['email'] == "another@unb.br"

    def test_user_read_user_not_found(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.get("/api/users/10", headers=headers)
        data = response.json()
        
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND
    
    def test_user_read_user_by_email_not_found(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.get(f"/api/users/email/invalid@unb.br", headers=headers)
        data = response.json()
        
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND
    
    def test_user_read_user(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.get(f"/api/users/{self.user1.id}", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        assert data['name'] == self.user1.name
        assert data['connection'] == self.user1.connection
        assert data['email'] == self.user1.email
        assert data['is_active'] == True
    
    def test_user_read_user_by_email(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.get(f"/api/users/email/{self.user1.email}", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        assert data['name'] == self.user1.name
        assert data['connection'] == self.user1.connection
        assert data['email'] == self.user1.email
    
    # Partial Update User
    def test_user_partial_update_user_invalid_connection(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.patch(f"/api/users/{self.user1.id}", json={"name": "NameZ", "email": "valid@email.com", "connection": "INVALIDO"}, headers=headers)
        data = response.json()
        
        assert response.status_code == 400
        assert data['detail'] == errorMessages.INVALID_CONNECTION
    
    def test_user_partial_update_user_not_found(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.patch(f"/api/users/10", json={"name": "NameZ"}, headers=headers)
        data = response.json()
        
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND
    
    def test_user_partial_update_user_already_registered_email(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.patch(f"/api/users/{self.user1.id}", json={"email": self.user2.email}, headers=headers)
        data = response.json()
        
        assert response.status_code == 400
        assert data['detail'] == errorMessages.EMAIL_ALREADY_REGISTERED
    
    def test_user_partial_update_user(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.patch(f"/api/users/{self.user1.id}", json={"name": "Updated Admin"}, headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        assert data['name'] == "Updated Admin"
        assert data['email'] == self.user1.email 
        assert data['connection'] == self.user1.connection
    
    # Update Role
    def test_user_update_role_not_authorized(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__user_access_token__}'}
        response = client.patch(f"/api/users/role/{self.user2.id}", json={"role": "ADMIN"}, headers=headers)
        data = response.json()
        
        assert response.status_code == 401
        assert data['detail'] == errorMessages.NO_PERMISSION
    
    def test_user_update_role_not_found(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.patch(f"/api/users/role/10", json={"role": "ADMIN"}, headers=headers)
        data = response.json()
        
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND
    
    def test_user_update_role_success(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.patch(f"/api/users/role/{self.user2.id}", json={"role": "ADMIN"}, headers=headers)
        data = response.json()
        
        assert response.status_code == 200
    
    # Delete User
    def test_user_delete_user_not_found(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.delete(f"/api/users/10", headers=headers)
        data = response.json()
        
        assert response.status_code == 404
        assert data['detail'] == errorMessages.USER_NOT_FOUND
    
    def test_user_delete_user_success(self):
        headers = {'Authorization': f'Bearer {test_auth.TestAuth.__admin_access_token__}'}
        response = client.delete(f"/api/users/{self.user3.id}", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        assert data['name'] == self.user3.name
        assert data['connection'] == self.user3.connection
        assert data['email'] == self.user3.email
        assert data['role'] == self.user3.role
        assert data['is_active'] == self.user3.is_active
