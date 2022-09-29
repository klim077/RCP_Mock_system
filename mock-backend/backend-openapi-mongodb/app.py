import connexion
from connexion.resolver import RestyResolver
from flask_cors import CORS


app = connexion.FlaskApp(
    __name__,
    specification_dir='specs/',
)

app.add_api(
    'sgym_v1_oas3.yml',
    resolver=RestyResolver('routes'),
    # validate_responses=True,
)

# Add CORS support, defaults to '*'
CORS(
    app=app.app,
    supports_credentials=True,
)


def main():
    app.run(
        port=9090,
        # ssl_context='adhoc'
    )


if __name__ == '__main__':
    main()
