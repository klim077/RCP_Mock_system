from setuptools import find_packages, setup


def get_version():
    with open('VERSION', 'r') as f:
        version = f.read()
    return version


setup(
    name='smartgymgatewayutils',
    version=get_version(),
    description='Common utilities used in SmartGym gateway',
    author='SmartGym',
    author_email='smartgym_support@tech.gov.sg',
    url='https://git.siotgov.tech/SmartGym/py-smartgym-gateway-utils.git',
    # packages=['smartgymgatewayutils'],  # same as name
    packages=find_packages(),
    install_requires=[
        'requests',
        'redis',
        'graypy',
        'paho-mqtt',
        'python-socketio[client]==4.6.1',
        'celery',
        'python-consul',
    ],  # external packages as dependencies
)
