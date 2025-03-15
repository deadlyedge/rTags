from fastapi import Depends, FastAPI
from routers import rtags, translate_subtitle
from fastapi.middleware.cors import CORSMiddleware
from utils.auth_utils import verify_token


app = FastAPI(title="API with Modular Routers", dependencies=[Depends(verify_token)])

# Routers
app.include_router(rtags.router, prefix="/rtags", tags=["rtags"])
app.include_router(translate_subtitle.router, prefix="/translate", tags=["translate"])

# CORS middleware
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
