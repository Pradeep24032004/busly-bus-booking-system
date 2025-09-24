
# main.py
import uvicorn
from fastapi import FastAPI
from routers import auth_routes, buses_routes, reservations_routes, admin_routes, users_routes, admin_topups 
from background_tasks import start_scheduler
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Bus Booking System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(auth_routes.router)
app.include_router(users_routes.router)               # <- ADDED
app.include_router(buses_routes.router)
app.include_router(reservations_routes.router)
app.include_router(admin_routes.router)
app.include_router(admin_topups.router)

@app.on_event("startup")
async def startup_event():
    # start background scheduler
    start_scheduler()

@app.get("/")
async def root():
    return {"message": "Bus booking backend running"}

# debug: list installed routes
@app.get("/__routes")
def list_routes():
    return [{"path": r.path, "methods": list(getattr(r, "methods", [])), "name": getattr(r.endpoint, "__name__", str(r.endpoint))} for r in app.routes if hasattr(r, "path")]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
