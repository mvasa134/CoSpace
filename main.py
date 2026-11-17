from fastapi import FastAPI
from app.routers import auth, coworkings, bookings, payments
import uvicorn

app = FastAPI(
    title="Coworking Booking API",
    description="без назви",
    version="1.0.0"
)


app.include_router(auth.router)
app.include_router(coworkings.router)
app.include_router(bookings.router)
app.include_router(payments.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Coworking API Service is running"}
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)