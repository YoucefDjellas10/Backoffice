from odoo import fields, models
import requests
import logging
_logger = logging.getLogger(__name__)


class ContactMessage(models.Model):
    _name = 'contact.message'
    _description = 'les message de contact de site'

    name = fields.Char(string='id', readonly=True)
    nom_complet = fields.Char(string='Nom Complet', readonly=True)
    email = fields.Char(string='E-mail', readonly=True)
    message = fields.Text(string='Message', readonly=True)
    client = fields.Many2one('liste.client', string='Client')
    create_date = fields.Datetime(string='Date')

    def appeler_api_disponibilite(self):
        # Données constantes pour l’exemple
        lieu_depart_id = 1
        lieu_retour_id = 2
        date_depart = "2025-08-20"
        heure_depart = "04:00"
        date_retour = "2025-08-26"
        heure_retour = "20:00"
        client_id = 10
        prime_code = "aze"

        # Construction de l’URL avec les paramètres
        base_url = "https://api.safarelamir.com/search-result/"
        params = {
            "lieu_depart_id": lieu_depart_id,
            "lieu_retour_id": lieu_retour_id,
            "date_depart": date_depart,
            "heure_depart": heure_depart,
            "date_retour": date_retour,
            "heure_retour": heure_retour,
            "client_id": client_id,
            "prime_code": prime_code
        }

        # Headers personnalisés
        headers = {
            "X-Country-Code": "DZ"
        }

        try:
            # Appel GET
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()  # Déclenche une exception si code HTTP != 200

            # Résultat JSON
            resultats = response.json()
            _logger.info("Résultats de l’API: %s", resultats)
            return resultats

        except requests.exceptions.RequestException as e:
            _logger.error("Erreur lors de l’appel à l’API externe: %s", str(e))
            return {"error": "Erreur de connexion à l’API"}
