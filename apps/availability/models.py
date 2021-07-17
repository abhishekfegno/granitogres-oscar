from django.conf import settings
from django.core.exceptions import ValidationError
from treebeard.mp_tree import MP_Node, MP_NodeManager
from django.contrib.gis.db import models


class PinCode(MP_Node):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    poly = models.PointField(null=True, blank=True)
    partners = models.ManyToManyField('partner.Partner',
                                      through='availability.PincodePartnerThroughModel',
                                      related_name='pincodes')
    objects = MP_NodeManager()

    COUNTRY_DEPTH = 1
    STATE_DEPTH = 2
    DISTRICT_DEPTH = 3
    COMMUNITY_DEPTH = 4
    POSTAL_CODE_DEPTH = 5

    def __str__(self):
        if self.code:
            return f"{self.name} - {self.code}"
        return self.name


class PincodePartnerThroughModel(models.Model):
    partner = models.ForeignKey('partner.Partner', on_delete=models.CASCADE, related_name='pincode_mappings')
    pincode = models.ForeignKey(PinCode, on_delete=models.CASCADE, related_name='partner_mappings')


class Zones(models.Model):
    name = models.CharField(max_length=128)
    zone = models.PolygonField()
    partner = models.ForeignKey('partner.Partner', related_name='zone', on_delete=models.CASCADE)
    pincode = models.ManyToManyField('availability.PinCode', )

    def clean(self):
        # qs = Zones.objects.all()
        # if self.pk:
        #     qs = qs.exclude(pk=self.pk)
        # overlapping_zone = qs.exclude(pk=self.pk).filter(zone__bboverlaps=self.zone).first()
        # if overlapping_zone:
        #     raise ValidationError(f'This Zone is overlapping with Zone: {overlapping_zone.name}!')
        pass



