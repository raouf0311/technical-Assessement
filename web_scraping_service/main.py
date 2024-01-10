from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
from httpx import AsyncClient
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# Define FastAPI app
app = FastAPI()

# Define SQLAlchemy models
Base = declarative_base()

class ScrapedData(Base):
    __tablename__ = "scraped_data"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Configure database connection
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to get a session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to scrape data from a Facebook page
async def scrape_facebook_page(page_url: str):
    async with AsyncClient() as client:
        response = await client.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Modify this based on the actual structure of the Facebook page
        data_content = soup.find('div', {'class': '_5rgt _5nk5'})
        return str(data_content)

# FastAPI endpoint to scrape and save data
@app.post("/scrape")
async def scrape_and_save(page_url: str, db: Session = Depends(get_db)):
    try:
        scraped_data = await scrape_facebook_page(page_url)
        db_data = ScrapedData(content=scraped_data)
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        return JSONResponse(content={"status": "success", "message": "Data scraped and saved successfully."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
