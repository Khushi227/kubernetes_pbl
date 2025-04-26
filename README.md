# FastAPI Pet Adoption and User Management System

This project is a **FastAPI-based application** that provides a pet adoption and user management system. It includes features for managing users, pets, and adoption processes, with secure authentication using **JWT tokens**.

---

## **Features**

### **1. User Management**
- **Register Users**: Create new user accounts with unique `username` and `email`.
- **Login Users**: Authenticate users and issue **JWT tokens** for secure session management.
- **Fetch Users**: Get all users or a specific user by their ID.
- **Protected Routes**: Access user-specific data using a valid JWT token.

### **2. Pet Management**
- **Add Pets**: Add new pets with details like `name`, `species`, and `age`.
- **Update/Delete Pets**: Modify or remove pets from the system.
- **List/Search Pets**: View all pets, or filter them by species or adoption status.

### **3. Adoption Management**
- **Adopt Pets**: Users can adopt pets, and the adoption history is recorded.
- **Adoption History**: View the adoption history of any pet.
- **User-Specific Pets**: Fetch all pets adopted by a specific user.

### **4. Recommendations**
- **Pet Recommendations**: Suggest pets to users based on their preferences or adoption history.

---

## **Tech Stack**
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Authentication**: JWT (via `python-jose`)
- **Password Hashing**: `passlib` (bcrypt algorithm)
- **Environment Variables**: `os.getenv` for managing secrets

---

## **Setup and Installation**

### **Prerequisites**
- Python 3.8+
- `pip` (Python package manager)

### **Installation**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-repo>/fastapi-pet-user-system.git
   cd fastapi-pet-user-system
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**:
   - Create a `.env` file in the root directory.
   - Add the following:
     ```
     SECRET_KEY=<your-secure-secret-key>
     ```

4. **Run the Application**:
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the API**:
   - Open your browser and go to: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to access the Swagger API documentation.

---

## **How to Use**

### **1. User Management**

#### **Register a New User**
```bash
curl -X POST http://127.0.0.1:8000/users/register -H "Content-Type: application/json" -d '{"username": "khushi", "email": "khushi@example.com", "password": "password123"}'
```

#### **Login a User**
```bash
curl -X POST http://127.0.0.1:8000/users/login -H "Content-Type: application/json" -d '{"username": "khushi", "password": "password123"}'
```
- **Response**:
  ```json
  {
      "access_token": "<your-jwt-token>",
      "token_type": "bearer"
  }
  ```

#### **Access Protected Route (Example)**
Use the token from the login response:
```bash
curl -X GET http://127.0.0.1:8000/users/me -H "Authorization: Bearer <your-jwt-token>"
```

#### **Fetch All Users**
```bash
curl -X GET http://127.0.0.1:8000/users
```

#### **Fetch User by ID**
```bash
curl -X GET http://127.0.0.1:8000/users/1
```

#### **Update User Preferences (Optional)**
```bash
curl -X PUT http://127.0.0.1:8000/users/1/preferences -H "Content-Type: application/json" -d '{"species": "dog", "age": {"min": 1, "max": 5}}'
```

---

### **2. Pet Management**

#### **Add a New Pet**
```bash
curl -X POST http://127.0.0.1:8000/pets -H "Content-Type: application/json" -d '{"name": "Buddy", "species": "dog", "age": 3}'
```

#### **Update a Pet**
```bash
curl -X PUT http://127.0.0.1:8000/pets/1 -H "Content-Type: application/json" -d '{"name": "Max", "species": "dog", "age": 4, "adopted": false}'
```

#### **Delete a Pet**
```bash
curl -X DELETE http://127.0.0.1:8000/pets/1
```

#### **List All Pets**
```bash
curl -X GET http://127.0.0.1:8000/pets
```

#### **Search for Pets**
```bash
curl -X GET "http://127.0.0.1:8000/pets/search?species=dog&adopted=false"
```

---

### **3. Adoption Management**

#### **Adopt a Pet**
```bash
curl -X POST http://127.0.0.1:8000/pets/1/adopt?user_id=1 -H "Authorization: Bearer <your-jwt-token>"
```

#### **Get Adoption History of a Pet**
```bash
curl -X GET http://127.0.0.1:8000/pets/1/history
```

#### **Get Pets Adopted by a User**
```bash
curl -X GET http://127.0.0.1:8000/users/1/pets
```

---

### **4. Recommendations**

#### **Get Pet Recommendations for a User**
```bash
curl -X GET http://127.0.0.1:8000/users/1/recommendations
```

---

## **Future Enhancements**

1. **Database Integration**:
   - Replace in-memory dictionaries with a persistent database (e.g., PostgreSQL, MongoDB).

2. **Role-Based Access Control (RBAC)**:
   - Add roles (e.g., admin, user) for restricted routes like adding or deleting pets.

3. **Enhanced Recommendations**:
   - Use machine learning or more advanced algorithms for personalized pet recommendations.

4. **Notification System**:
   - Notify users when a pet matching their preferences is added.

5. **Password Reset**:
   - Implement a password reset feature via email.

---

## **Contributing**

Contributions are welcome! Please fork the repository and submit a pull request.

---

## **License**

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.