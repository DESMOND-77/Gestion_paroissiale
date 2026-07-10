from rest_framework import serializers


class WritableIDModelSerializer(serializers.ModelSerializer):
    """ModelSerializer dont la clé primaire UUID est fournie par le client.

    Par défaut DRF rend la clé primaire *read-only*, ce qui empêcherait le
    frontend offline d'imposer l'UUID qu'il a généré hors ligne (le serveur en
    régénérerait un et provoquerait des doublons à la synchro). On redéclare
    donc `id` modifiable et optionnel :

    - fourni par le client → respecté (indispensable pour l'offline-first) ;
    - absent → le serveur en génère un (`default=uuid4`).

    La réassignation de la clé primaire lors d'une mise à jour est interdite
    (une PUT ne doit jamais déplacer un enregistrement vers un autre id).
    """

    id = serializers.UUIDField(required=False)

    def update(self, instance, validated_data):
        validated_data.pop("id", None)
        return super().update(instance, validated_data)
