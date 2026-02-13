from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PeluqueriaServicio(models.Model):
    _name = 'peluqueria.servicio'
    _description = 'Servicios de Peluquería'

    name = fields.Char(string='Nombre del Servicio', required=True)
    
    precio_base = fields.Float(string='Precio Base')
    duracion = fields.Float(string='Duración (Horas)')
    descripcion = fields.Text(string='Descripción')

    imagen = fields.Binary(string="Imagen")

    # Validar valores positivos (Precio)
    @api.constrains('precio_base')
    def _check_precio_positivo(self):
        for record in self:
            if record.precio_base < 0:
                raise ValidationError("El precio no puede ser negativo.")
            
    # Validar valores positivos (Duración)
    @api.constrains('duracion')
    def _check_duracion_positiva(self):
        for record in self:
            if record.duracion < 0:
                raise ValidationError("La duración no puede ser negativa.")