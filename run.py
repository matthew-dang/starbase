from app import create_app, db


app = create_app()

with app.app_context():
    print("Test")
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 
