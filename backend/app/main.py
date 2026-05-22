import uvicorn


def main():
    print("Hello from backend!")
    
    uvicorn.run("app.factory:create_app",
        factory = True,
        host = "0.0.0.0",
        port = 8000,
        reload = True,
        log_level = "debug",
        access_log = True,)


if __name__ == "__main__":
    main()
