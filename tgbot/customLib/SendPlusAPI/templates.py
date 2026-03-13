templates = {
    'operator': {
        'kaz': {
            "name": "operator_answer_kz",
            "components": [
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": {
                                "to_chain_id": "67acf3537a57889fd40ac745"
                            }
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 1,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": {
                                "to_chain_id": "67acf446b645f631770cea84"
                            }
                        }
                    ]
                }
            ],
            "language": {
                "policy": "deterministic",
                "code": "kk"
            }
        },
        'rus': {
            "name": "operator_answer",
            "components": [
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": {
                                "to_chain_id": "67ac8825407f2aaded04443b"
                            }
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 1,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": {
                                "to_chain_id": "67ac5237c67bc82a3109abcd"
                            }
                        }
                    ]
                }
            ],
            "language": {
                "policy": "deterministic",
                "code": "ru"
            }
        }
    },
    'grade': {
        'kaz': {
            "name": "client_grade_kz",
            "components": [
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": {
                                "to_chain_id": "67acf3dbdbfeb679e3095dac"
                            }
                        }
                    ]
                }
            ],
            "language": {
                "policy": "deterministic",
                "code": "kk"
            }
        },
        'rus': {
            "name": "client_grade",
            "components": [
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": {
                                "to_chain_id": "67abad1f428ba8fc9208df1c"
                            }
                        }
                    ]
                }
            ],
            "language": {
                "policy": "deterministic",
                "code": "ru"
            }
        }
    }
}

