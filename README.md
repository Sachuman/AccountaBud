# LaHacks-2025

## Install `uv`
```bash
brew install uv
```

## Create the Virtual Environment
```bash
uv sync
source .venv/bin/activate
```

## Start the Server
```bash
uv run fastapi dev
```

## Add Dependency
```bash
uv add <package_name>
```

## API Endpoints

### Action API

#### Create Action
```
POST /action
```
Creates a new action (restriction or reminder).

Request Body:
```json
{
  "date": "2024-05-01",
  "time": "14:30",
  "website": "example.com",
  "description": "Description of the action",
  "type": "restriction",
  "phone": "+1234567890"  // Required for reminders
}
```

#### Get All Actions
```
GET /action
```
Returns all actions.

#### Check Website Restriction
```
GET /action/restriction/{website}
```
Checks if a website is restricted. Returns `{"restricted": true}` if restricted.

#### Get All Reminders
```
GET /action/reminder
```
Returns all reminders.

### Dependencies

Make sure to set the following environment variables:
- `MONGODB_URI`: MongoDB connection string (defaults to "mongodb://localhost:27017")
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER`: Your Twilio Phone Number
