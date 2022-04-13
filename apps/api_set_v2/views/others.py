from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers, status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.conf import settings

from apps.api_set_v2.serializers.catalogue import BrochureSerializer, GallerySerializer
from apps.dashboard.custom.models import NewsLetter, Brochure, Gallery

normalize = lambda request: request.POST if request.POST.keys() else (request.data if request.data.keys() else  request.query_params)


class NewsLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsLetter
        fields = ('email', )


class NewsLetterAPIView(CreateAPIView):
    queryset = NewsLetter.objects.all()
    serializer_class = NewsLetterSerializer


class SendEmail(APIView):

    """


    """
    permission_classes = (AllowAny, )

    def post(self, request):
        """
        :param request:
        :return:
        """
        out = {'status': 'failed'}
        body = normalize(request)
        recep = [settings.WEBSITE_EMAIL_RECEIVER, ]

        from datetime import datetime
        time = (datetime.now()).strftime('%a %H:%M  %d/%m/%y')
        _ = send_mail(
            subject="Received a Response from %s" % body.get('name'),
            message="""
            NAME : {name}
            MOBILE : {mobile} 
            EMAIL : {email}
            ==============================================
            MESSAGE  : {message}
            ==============================================
           
            """.format(**body, time=time),
            from_email=settings.WEBSITE_EMAIL_RECEIVER,
            recipient_list=[body.get('email')], fail_silently=False)
        out['status'] = 'email_sent'
        out['mail_content'] = str(_)
        return Response(out)


class BrochureListView(GenericAPIView):
    queryset = Brochure.objects.all()
    serializer_class = BrochureSerializer
    success_url = 'dashboard:brochure-create'

    def get(self, request, *args, **kwargs):
        type = self.kwargs.get('type')
        serializer = self.serializer_class(self.get_queryset().filter(type=type), context={'request': request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GalleryListView(GenericAPIView):
    queryset = Gallery.objects.all()
    serializer_class = GallerySerializer
    success_url = 'dashboard:gallery-create'

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(self.get_queryset(), context={'request': request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)