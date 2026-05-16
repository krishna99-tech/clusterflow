from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from datetime import datetime
import socket
import uvicorn
from pathlib import Path

# =====================================================
# FastAPI App
# =====================================================

app = FastAPI()

# =====================================================
# Static Files
# =====================================================

static_path = Path(__file__).parent / "static"

if static_path.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_path)),
        name="static"
    )

# =====================================================
# Templates
# =====================================================

templates_path = Path(__file__).parent / "templates"

templates = Jinja2Templates(
    directory=str(templates_path)
)

hostname = socket.gethostname()

# =====================================================
# MongoDB Connection
# =====================================================

MONGO_URL = "mongodb://192.168.0.179:27017"

mongo_client = AsyncIOMotorClient(MONGO_URL)

db = mongo_client["business_system"]

products_collection = db["products"]
employees_collection = db["employees"]

# =====================================================
# Pydantic Models
# =====================================================

class Product(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    quantity: int
    description: str
    created_date: datetime


class Employee(BaseModel):
    employee_id: str
    name: str
    department: str
    position: str
    salary: float
    email: str
    hire_date: datetime


# =====================================================
# API Routes
# =====================================================

@app.post("/products")
async def add_product(data: Product):

    product_data = data.dict()

    await products_collection.insert_one(product_data)

    return {
        "status": "saved",
        "product_id": data.product_id,
        "server": hostname
    }


@app.get("/products")
async def get_products():

    data = []

    async for product in products_collection.find({}, {"_id": 0}):
        data.append(product)

    return data


@app.get("/products/{product_id}")
async def get_product(product_id: str):

    data = []

    async for product in products_collection.find(
        {"product_id": product_id},
        {"_id": 0}
    ):
        data.append(product)

    return data


@app.post("/employees")
async def add_employee(data: Employee):

    employee_data = data.dict()

    await employees_collection.insert_one(employee_data)

    return {
        "status": "saved",
        "employee_id": data.employee_id,
        "server": hostname
    }


@app.get("/employees")
async def get_employees():

    data = []

    async for employee in employees_collection.find({}, {"_id": 0}):
        data.append(employee)

    return data


@app.get("/employees/{employee_id}")
async def get_employee(employee_id: str):

    data = []

    async for employee in employees_collection.find(
        {"employee_id": employee_id},
        {"_id": 0}
    ):
        data.append(employee)

    return data


# =====================================================
# API - Latest Records
# =====================================================

@app.get("/api/latest-product")
async def api_latest_product():

    data = await products_collection.find_one(
        sort=[("created_date", -1)],
        projection={"_id": 0}
    )

    return data or {}


@app.get("/api/latest-employee")
async def api_latest_employee():

    data = await employees_collection.find_one(
        sort=[("hire_date", -1)],
        projection={"_id": 0}
    )

    return data or {}


# =====================================================
# HTML Dashboard
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    products = []
    employees = []

    latest_product = None
    latest_employee = None

    total_products = 0
    total_employees = 0

    try:

        # Products
        async for product in products_collection.find(
            {},
            {"_id": 0}
        ).sort("created_date", -1):

            products.append(product)

        total_products = len(products)

        if products:
            latest_product = products[0]

        # Employees
        async for employee in employees_collection.find(
            {},
            {"_id": 0}
        ).sort("hire_date", -1):

            employees.append(employee)

        total_employees = len(employees)

        if employees:
            latest_employee = employees[0]

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "server": hostname,
            "products": products[:20],
            "employees": employees[:20],
            "latest_product": latest_product,
            "latest_employee": latest_employee,
            "total_products": total_products,
            "total_employees": total_employees
        }
    )


# =====================================================
# Add Product Form
# =====================================================

@app.post("/add-product")
async def add_product_form(
    request: Request,
    product_id: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    description: str = Form(...),
    created_date: str = Form(...)
):

    try:

        product_created_date = datetime.fromisoformat(created_date)

        product_data = {
            "product_id": product_id,
            "name": name,
            "category": category,
            "price": price,
            "quantity": quantity,
            "description": description,
            "created_date": product_created_date
        }

        await products_collection.insert_one(product_data)

        return RedirectResponse(
            url="/?message=Product added successfully!",
            status_code=303
        )

    except Exception as e:

        print(f"Error adding product: {e}")

        return RedirectResponse(
            url="/?message=Error adding product&message_type=danger",
            status_code=303
        )


# =====================================================
# Add Employee Form
# =====================================================

@app.post("/add-employee")
async def add_employee_form(
    request: Request,
    employee_id: str = Form(...),
    name: str = Form(...),
    department: str = Form(...),
    position: str = Form(...),
    salary: float = Form(...),
    email: str = Form(...),
    hire_date: str = Form(...)
):

    try:

        employee_hire_date = datetime.fromisoformat(hire_date)

        employee_data = {
            "employee_id": employee_id,
            "name": name,
            "department": department,
            "position": position,
            "salary": salary,
            "email": email,
            "hire_date": employee_hire_date
        }

        await employees_collection.insert_one(employee_data)

        return RedirectResponse(
            url="/?message=Employee added successfully!",
            status_code=303
        )

    except Exception as e:

        print(f"Error adding employee: {e}")

        return RedirectResponse(
            url="/?message=Error adding employee&message_type=danger",
            status_code=303
        )


# =====================================================
# View Product
# =====================================================

@app.get("/product/view/{product_id}", response_class=HTMLResponse)
async def view_product(
    request: Request,
    product_id: str
):

    product = None

    try:

        product = await products_collection.find_one(
            {"product_id": product_id},
            {"_id": 0}
        )

    except Exception as e:

        print(f"Error fetching product: {e}")

    return templates.TemplateResponse(
        request=request,
        name="view_product.html",
        context={
            "product_id": product_id,
            "product": product,
            "server": hostname
        }
    )


# =====================================================
# Delete Product
# =====================================================

@app.post("/delete-product")
async def delete_product_form(
    request: Request,
    product_id: str = Form(...)
):

    try:

        result = await products_collection.delete_one(
            {"product_id": product_id}
        )

        if result.deleted_count > 0:
            message = "Product deleted successfully!"
        else:
            message = "Product not found!"

        return RedirectResponse(
            url=f"/?message={message}",
            status_code=303
        )

    except Exception as e:

        print(f"Error deleting product: {e}")

        return RedirectResponse(
            url="/?message=Error deleting product&message_type=danger",
            status_code=303
        )


# =====================================================
# View Employee
# =====================================================

@app.get("/employee/view/{employee_id}", response_class=HTMLResponse)
async def view_employee(
    request: Request,
    employee_id: str
):

    employee = None

    try:

        employee = await employees_collection.find_one(
            {"employee_id": employee_id},
            {"_id": 0}
        )

    except Exception as e:

        print(f"Error fetching employee: {e}")

    return templates.TemplateResponse(
        request=request,
        name="view_employee.html",
        context={
            "employee_id": employee_id,
            "employee": employee,
            "server": hostname
        }
    )


# =====================================================
# Delete Employee
# =====================================================

@app.post("/delete-employee")
async def delete_employee_form(
    request: Request,
    employee_id: str = Form(...)
):

    try:

        result = await employees_collection.delete_one(
            {"employee_id": employee_id}
        )

        if result.deleted_count > 0:
            message = "Employee deleted successfully!"
        else:
            message = "Employee not found!"

        return RedirectResponse(
            url=f"/?message={message}",
            status_code=303
        )

    except Exception as e:

        print(f"Error deleting employee: {e}")

        return RedirectResponse(
            url="/?message=Error deleting employee&message_type=danger",
            status_code=303
        )


# =====================================================
# Run Server
# =====================================================

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )