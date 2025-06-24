# Environment Variables

This application requires the following environment variables to be set. Create a `.env` file in the backend directory with the following variables:

## Required Environment Variables

### Database Configuration
```
DATABASE_URL=sqlite:///./novalearn.db
```

### Security Configuration
```
SECRET_KEY=your-secret-key-here-change-in-production
```

### JWT Configuration
```
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Example .env file
```
DATABASE_URL=sqlite:///./novalearn.db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Notes
- The `.env` file should be added to `.gitignore` to keep sensitive information out of version control
- For production, use a strong, randomly generated SECRET_KEY
- The DATABASE_URL can be changed to use PostgreSQL, MySQL, or other databases 