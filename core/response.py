def standardized_response(success=True, data=None, error=None, message=None, **kwargs):
    """Fonction utilitaire pour standardiser les réponses API.

    Args:
        success (bool): Indique si la requête a réussi.
        Data (any): Les données à retourner en cas de succès.
        error (str): Message d'erreur en cas d'échec.
        message (str): Message informatif.
        **kwargs: Arguments supplémentaires à inclure dans la réponse.

        Returns:
            dict: Dictionnaire formaté pour la réponse API.
    """
    response = {"success": success}

    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    if message is not None:
        response["message"] = message
    for key, value in kwargs.items():
        response[key] = value
    return response
