from fastapi import FastAPI
from db.database import engine, Base, SessionLocal
from routers import api_controller, dashboard_controller
from services.demo_service import demo_service
from services.server_key_holder import server_key_holder
import contextlib
import logging     

logging.basicConfig(level=logging.INFO)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure keys are generated
    _ = server_key_holder.get_public_key_base64()
    
    # Startup: create tables and seed demo accounts
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        demo_service.seed_accounts(db)
    finally:
        db.close()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(dashboard_controller.router)
app.include_router(api_controller.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
