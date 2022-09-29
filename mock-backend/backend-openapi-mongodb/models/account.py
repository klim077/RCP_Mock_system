#!/usr/bin/python
# -*- coding: utf-8 -*-
from werkzeug.security import safe_str_cmp
from flask import jsonify
import flask_bcrypt
from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError
import datetime


# ------------------------------------------------------------------------------
# CLASS IDENTITY
# ------------------------------------------------------------------------------
class SessionIdentity:
    # --------------------------------------------------------------------------
    # CONSTRUCTOR METHOD
    # --------------------------------------------------------------------------
    def __init__(self, id, username, name, gender):
        self.id = id
        self.username = username
        self.name = name
        self.gender = gender
        # self.email = email

    # --------------------------------------------------------------------------
    # METHOD STR
    # --------------------------------------------------------------------------
    def as_json(self):
        return jsonify({
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "gender": self.gender,
            # "email": self.email
        })


# ------------------------------------------------------------------------------
# CLASS USER
# ------------------------------------------------------------------------------
# Represents a User in SGym
signup_schema = {
    "type": "object",
    "properties": {
        "gender": {
            "type": "string",
        },
        "username": {
            "type": "string",
            "format": "string"
        },
        "password": {
            "type": "string",
            "minLength": 5
        },
        "displayname": {
            "type": "string",
            "format": "string"
        },
        "phonenumber": {
            "type": "string",
            "format": "string"
        },
    },
    "required": ["username", "password"],
    "additionalProperties": False
}

activeSg_signup_schema = {
    "type": "object",
    "properties": {
        "activeSgId": {
            "type": "string",
        },
        "phoneNo": {
            "type": "string",
        },
        "location": {
            "type": "string",
        },
        "device": {
            "type": "string",
        },
        "machineUUID": {
            "type": "string",
        }
    },
    "required": ["activeSgId", "phoneNo", "location", "device", "machineUUID"],
    "additionalProperties": False
}
# Function to convert number into string
# Switcher is dictionary data type here


def schemas(argument):
    switcher = {
        0: signup_schema,
        1: activeSg_signup_schema,
    }

    # get() method of dictionary data type returns
    # value of passed argument if it is present
    # in dictionary otherwise second argument will
    # be assigned as default value of passed argument
    return switcher.get(argument, 0)

# --------------------------------------------------------------------------
# JSON VALIDATION
# --------------------------------------------------------------------------


def validate_user(data, options):
    try:
        validate(data, schemas(options))
    except ValidationError as e:
        return {'ok': False, 'message': e}
    except SchemaError as e:
        return {'ok': False, 'message': e}

    return {'ok': True, 'data': data}

# --------------------------------------------------------------------------
# METHOD AUTHENTICATE
# --------------------------------------------------------------------------


def authenticate(self, password):
    return True
    #challenge = compute_hash(password, self.salt)
    # return safe_str_cmp(self.password.encode('utf-8'), challenge.encode('utf-8'))

# --------------------------------------------------------------------------
# METHOD UPDATE PASSWORD
# --------------------------------------------------------------------------


def update_password(self, password):
    self.password = flask_bcrypt.generate_password_hash(password)
    return True
