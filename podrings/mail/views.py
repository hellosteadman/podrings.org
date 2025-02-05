from django.urls import reverse
from django.views.generic import FormView, TemplateView
from .forms import PreferencesForm


class PreferencesView(FormView):
    form_class = PreferencesForm
    template_name = 'mail/preferences_form.html'

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'email_hash': self.kwargs['email_hash']
        }

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('mail_preferences_updated')


class PreferencesUpdatedView(TemplateView):
    template_name = 'mail/preferences_updated.html'


class PreviewView(TemplateView):
    template_name = 'mail/message.html'

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'subject': 'Email subject',
            'image_url': 'https://placehold.co/500x281',
            'body': (
                'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque vestibulum lorem non pellentesque pellentesque.\n\n'
                'Nam venenatis placerat orci, ac fermentum lectus pharetra id. Nunc ac pharetra nisl, sed ultrices eros..\n\n'
                'Sed aliquam tristique est, ac ultricies velit efficitur quis. Quisque facilisis consequat eleifend..\n\n'
                'Nulla facilisi. Donec dignissim justo et lectus faucibus laoreet..\n\n'
                'Morbi nec tempus mauris. Maecenas at elementum neque, et finibus velit. Donec commodo ornare ultrices..\n\n'
                'Donec aliquet orci nulla, id faucibus lorem varius vitae. Suspendisse et erat tempus, malesuada velit tempus, gravida velit..\n\n'
                'In hac habitasse platea dictumst.'
            ),
            'primary_url': 'javascript:;',
            'primary_cta': 'Call to action',
            'preferences_url': 'javascript:;',
            'footer_links': [
                {
                    'url': 'javascript:;',
                    'title': 'First footer link'
                },
                {
                    'url': 'javascript:;',
                    'title': 'Second footer link'
                }
            ]
        }
