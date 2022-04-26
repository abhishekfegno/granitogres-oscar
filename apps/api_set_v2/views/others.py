from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework import serializers, status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.conf import settings

from apps.api_set_v2.serializers.catalogue import BrochureSerializer, GallerySerializer
from apps.dashboard.custom.models import NewsLetter, Brochure, Gallery
from apps.utils.urls import list_api_formatter

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
    {
        "title": "RFQ" or "Contact",
        "name":,
        "email":,
        "mobile":,
        "message":
    }
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
        if body.get('title') == 'Contact' or None :
            subject = "Received a Response from %s" % body.get('name'),
        elif body.get('title') == 'RFQ':
            subject = "Request from Quotation "
        import pdb;pdb.set_trace()
        time = (datetime.now()).strftime('%a %H:%M  %d/%m/%y')
        _ = send_mail(
            subject=subject,
            message="""
            TITLE :{title},
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
    queryset = Brochure.objects.all().order_by('-id')
    serializer_class = BrochureSerializer
    success_url = 'dashboard:brochure-create'

    def get(self, request, *args, **kwargs):
        type = self.request.GET.get('type')
        page_number = int(self.request.GET.get('page', '1'))
        page_size = int(request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))

        if type:
            queryset = self.get_queryset().filter(type=type)
        else:
            queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, context={'request': request}, many=True)

        paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
        empty_list = False
        try:
            page_number = paginator.validate_number(page_number)
        except PageNotAnInteger:
            page_number = 1
        except EmptyPage:
            page_number = paginator.num_pages
            empty_list = True
        page_obj = paginator.get_page(page_number)
        data = list_api_formatter(request, paginator, page_obj, results=serializer.data)
        return Response(data, status=status.HTTP_200_OK)


class GalleryListView(GenericAPIView):
    queryset = Gallery.objects.all().order_by('-id')
    serializer_class = GallerySerializer
    success_url = 'dashboard:gallery-create'

    def get(self, request, *args, **kwargs):
        page_number = int(self.request.GET.get('page', '1'))
        page_size = int(request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))
        serializer = self.serializer_class(self.get_queryset(), context={'request': request}, many=True)
        paginator = Paginator(self.get_queryset(), page_size)  # Show 18 contacts per page.
        empty_list = False
        try:
            page_number = paginator.validate_number(page_number)
        except PageNotAnInteger:
            page_number = 1
        except EmptyPage:
            page_number = paginator.num_pages
            empty_list = True
        page_obj = paginator.get_page(page_number)
        data = list_api_formatter(request, paginator, page_obj, results=serializer.data)
        return Response(data, status=status.HTTP_200_OK)
