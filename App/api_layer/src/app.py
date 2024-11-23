from fastapi.responses import JSONResponse
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from model.alert import Alert
from model.settings import DashboardSettings
from notification_service import send_notification, retrieve_alerts
from user_settings_service import persist_user_settings, retrieve_user_settings
from database.connection import get_db_connection
from constants import *
import logging

from api_auth import get_verify_api_key
from model.user import *
from typing import Annotated
import json


app = FastAPI()
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/smartfactory/postAlert")
async def post_alert(alert: Alert, api_key: str = Depends(get_verify_api_key(["data"]))):
    """
    Endpoint to post an alert.
    This endpoint receives an alert object and processes it by sending notifications
    based on the alert's properties. It performs several validation checks on the 
    alert object before sending the notification.
    Args:
        alert (Alert): The alert object containing notification details.
    Returns:
        Response: A response object with status code 200 if the notification is sent successfully.
    Raises:
        HTTPException: If any validation check fails or an unexpected error occurs.
    """

    try:
        logging.info("Received alert with title: %s", alert.description)
        
        if not alert.title:
            logging.error("Missing notification title")
            raise HTTPException(status_code=400, detail="Missing notification title")
        
        if not alert.description:
            logging.error("Missing notification description")
            raise HTTPException(status_code=400, detail="Missing notification description")
        
        if not alert.isPush and not alert.isEmail:
            logging.error("No notification method selected")
            raise HTTPException(status_code=400, detail="No notification method selected")
        
        if not alert.recipients or len(alert.recipients) == 0:
            logging.error("No recipients specified")
            raise HTTPException(status_code=400, detail="No recipients specified")
        
        logging.info("Sending notification")
        send_notification(alert)
        logging.info("Notification sent successfully")

        return JSONResponse(content={"message": "Notification sent successfully"}, status_code=200)
    except HTTPException as e:
        logging.error("HTTPException: %s", e.detail)
        raise e
    except ValueError as e:
        logging.error("ValueError: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except TypeError as e:
        logging.error("TypeError: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error("Exception: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.error("Exception: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/smartfactory/alerts/{userId}")
def get_alerts(userId: str, api_key: str = Depends(get_verify_api_key(["gui"]))):
    """
    Retrieve alerts for a given user and return them as a JSON response.

    Args:
        userId (str): The ID of the user for whom to retrieve alerts.

    Returns:
        JSONResponse: A JSON response containing the list of alerts for the user.
    """
    logging.info("Retrieving alerts for user: %s", userId)
    list = retrieve_alerts(userId)
    logging.info("Alerts retrieved successfully for user: %s", userId)

    return JSONResponse(content={"alerts": list}, status_code=200)

@app.post("/smartfactory/settings/{userId}")
def save_user_settings(userId: str, settings: dict, api_key: str = Depends(get_verify_api_key(["gui"]))):
    """
    Endpoint to save user settings.
    This endpoint receives a user ID and a JSON object with the settings to be saved.
    Args:
        userId (str): The ID of the user.
        settings (dict): The settings to be saved.
    Returns:
        Response: A response object with status code 200 if the settings are saved successfully.
    Raises:
        HTTPException: If an unexpected error occurs.
    """
    try:
        persist_user_settings(userId, settings)
        return JSONResponse(content={"message": "Settings saved successfully"}, status_code=200)
    except Exception as e:
        logging.error("Exception: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/smartfactory/settings/{userId}")
def get_user_settings(userId: str, api_key: str = Depends(get_verify_api_key(["gui"]))):
    """
    Endpoint to get user settings.
    This endpoint receives a user ID and returns the settings for that user.
    Args:
        userId (str): The ID of the user.
    Returns:
        dict: A dictionary containing the user settings.
    Raises:
        HTTPException: If an unexpected error occurs.
    """
    try:
        settings = retrieve_user_settings(userId)
        return JSONResponse(content=settings, status_code=200)
    except Exception as e:
        logging.error("Exception: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/smartfactory/login")
def login(body: Login):
    """
    Endpoint to login a user.
    This endpoint receives the user credentials and logins the user if it is present in the database.
    Args:
        body (LoginModel): the login body object containing the login details.
    Returns:
        UserInfo object with the details of the user logged in.
    Raises:
        HTTPException: If any validation check fails or an unexpected error occurs.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT Id, Username, Type, Email, Password FROM Users WHERE "+("Email" if body.isEmail else "Username")+"=\'%s\'"
        cursor.execute(query, (body.user))
        results = cursor.fetchall()
        logging.info(results)
        #TODO check results
        '''if (not_found):
            raise HTTPException(status_code=404, detail="User not found")
        elif (wrong_psw):
            raise HTTPException(status_code=400, detail="Wrong credentials")'''
        resp = UserInfo()
        return resp
    except HTTPException as e:
        logging.error("HTTPException: %s", e.detail)
        raise e
    except Exception as e:
        logging.error("Exception: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/smartfactory/logout")
def logout(userId: str):
    """
    Endpoint to logout a user.
    This endpoint receives the userId and logouts the user if it is present in the database.
    Args:
        body (userId): the id of the user to logout.
    Returns:
        JSONResponse 200
    Raises:
        HTTPException: If the user is not present in the database.
    """
    #TODO logout DB
    if (not_found):
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content={"message": "User logged out successfully"}, status_code=200)

@app.post("/smartfactory/register", status_code=status.HTTP_201_CREATED)
def register(body: Register):
    """
    Endpoint to register a user.
    This endpoint receives the user info and inserts a new user if it is not present in the database.
    Args:
        body (Register): the user details of the new user.
    Returns:
        UserInfo object with the details of the user created.
    Raises:
        HTTPException: If the user is already present in the database.
    """
    #TODO register DB
    if (found):
        raise HTTPException(status_code=400, detail="User already registered")
    return UserInfo()

@app.get("/smartfactory/dashboardSettings/{dashboardId}")
def load_dashboard_settings(dashboardId: str):
    '''
    Endpoint to load dashboard settings from the Database.
    This endpoint receives a dashboard ID and returns the corresponding settings fetched from the DB.
    Args:
        dashboardId (str): The ID of the dashboard.
    Returns:
        dashboard_settings: DashboardSettings object containing the settings.
    Raises:
        HTTPException: If the settings are not found or an unexpected error occurs.

    '''
    pass # Placeholder for the implementation

@app.post("/smartfactory/dashboardSettings/{dashboardId}")
def save_dashboard_settings(dashboardId: str, dashboard_settings: DashboardSettings):
    '''
    Endpoint to save dashboard settings to the Database.
    This endpoint receives a dashboard ID and the settings to be saved and saves them to the DB.
    Args:
        dashboardId (str): The ID of the dashboard.
        dashboard_settings (DashboardSettings): The settings to be saved.
    Returns:
        Response: A response object with status code 200 if the settings are saved successfully.
    Raises:
        HTTPException: If the settings are invalid or an unexpected error occurs.
        
    '''
    pass # Placeholder for the implementation


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")