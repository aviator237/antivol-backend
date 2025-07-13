from __future__ import print_function
from django.http import Http404
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail, EmailMessage
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.handlers.wsgi import WSGIRequest
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.html import strip_tags
from authentification.models import Otp
from rest_framework_simplejwt.tokens import RefreshToken
from box.models import Box
from account.models import UserRole, Profil
from notification.utils import NotificationService
from .forms import UserRegistrationForm, CompanyOwnerRegistrationForm, CompanyCreationForm, CombinedCompanyRegistrationForm
from django.contrib.auth.decorators import login_required
from .token import TokenGenerator
import clicksend_client
from clicksend_client import SmsMessage
from clicksend_client.rest import ApiException
from django.conf import settings
import threading

# Configure HTTP basic authorization: BasicAuth
configuration = clicksend_client.Configuration()
configuration.username = settings.CLICK_SEND_USERNAME
configuration.password = settings.CLICK_SEND_API_KEY


#
def register(request: WSGIRequest, mac_address: str):
    if request.user.is_authenticated:
        return redirect("/account")

    target_device: Box = Box.objects.filter(mac_address=mac_address)
    if target_device:
        target_device = target_device[0]
    else:
        raise Http404("Boxe non trouvé")
    next = request.GET.get("next")

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['phone_number']
            user.set_password(form.cleaned_data['password'])
            user.is_active = False
            user.save()
            if target_device:
                target_device.owner = user
                target_device.save()

            uid = urlsafe_base64_encode(force_bytes(user.id))

            messages.success(request, "Votre compte a été créé avec succès ! Nous vous avons envoyé un message d'activation")
            NotificationService().phone_number_verifiynig(target_device)

            threading.Thread(target=sendActivationSMS, args=(user, )).start()
            return redirect(f"/auth/activate?next={next}&ma={mac_address}&uid={urlsafe_base64_encode(force_bytes(user.id))}")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserRegistrationForm()
    NotificationService().notify_account_creation(target_device)
    return render(request, "auth/register.html", context={"title": "Création de compte", "next": next, 'mac_address': mac_address, 'form': form})


def log_in(request: WSGIRequest):
    if request.user.is_authenticated:
        return redirect("/account")
    next = request.GET.get("next")
    mac_address = request.GET.get("ma")
    email_sent = request.GET.get("email_sent")

    # Show message if redirected from company registration with email sent
    if email_sent == "true":
        messages.success(request, "Un email d'activation a été envoyé à votre adresse email. Veuillez vérifier votre boîte de réception et cliquer sur le lien d'activation.")
    if request.POST:
        login_value = request.POST.get("login")
        password = request.POST.get("password")
        user = authenticate(request, username=login_value, password=password)
        if user is None:
            user = authenticate(request, username=User.objects.filter(email=login_value).first(), password=password)
        if user is not None:
            if user.is_active == False:
                messages.error(request, "Vous n'avez pas encore activé votre compte; veuillez verifier votre adresse email")
                return redirect(f"/auth/login?next={next}&ma={mac_address}" if next is not None else f"/auth/login?ma={mac_address}")
            login(request, user)
            target_device = Box.objects.filter(owner=user)
            if target_device:
                target_device = target_device[0]
                target_device.owner = user
                target_device.save()
                refresh = RefreshToken.for_user(user)
                NotificationService().renew_token(target_device,
                {"access": str(refresh.access_token), "refresh": str(refresh)})
                NotificationService().close_window(target_device)
            elif mac_address is not None:
                target_device = Box.objects.filter(mac_address=mac_address)
                if target_device:
                    target_device = target_device[0]
                    target_device.owner = user
                    target_device.save()
                    refresh = RefreshToken.for_user(user)
                    NotificationService().renew_token(target_device,
                    {"access": str(refresh.access_token), "refresh": str(refresh)})
                    NotificationService().close_window(target_device)
            messages.success(request, "Authentification réussie")
            if next is not None and str(next).lower() != "none":
                return redirect(f"{next}?ma={mac_address}")
            profil = Profil.objects.get(owner=user)
            if profil is not None and profil.is_company_owner():
                print("C'est un damin d'entreprise********************")
                return redirect(f"/company")
            return redirect(f"/account?ma={mac_address}")
        else:
            expected_user = User.objects.filter(username=login_value)
            if expected_user:
                if not expected_user[0].is_active:
                    messages.error(request, "Votre compte n'est pas activé. Nous vous avons envoyé un mail d'activation")
                else:
                    messages.error(request, "L'authentification a échoué")
            else:
                messages.error(request, "L'authentification a échoué")
            return redirect(f"/auth/login?next={next}&ma={mac_address}" if next is not None else f"/auth/login?ma={mac_address}")
    else:
        return render(request, "auth/login.html", context={"title": "Connexion", "next": next, 'mac_address': mac_address})

def log_out(request: WSGIRequest):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect("/auth/login")

def resent(request):
    next = request.GET.get("next")
    uidb64 = request.GET.get("uid")
    ma = request.GET.get("ma")
    messages.success(request, "Un nouveau code d'activation a été envoyé sur votre numéro de téléphone")
    threading.Thread(target=sendActivationSMS, args=(request.user, )).start()
    return redirect(f"/auth/activate?next={next}&ma={ma}&uid={uidb64}")


def activate(request: WSGIRequest):
    next = request.GET.get("next")
    token = request.GET.get("token")
    uidb64 = request.GET.get("uid")
    ma = request.GET.get("ma")

    # Handle direct activation from email link
    if token and uidb64 and not request.POST:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            myUser = User.objects.get(id=int(uid))
            otp_instance = Otp.objects.get(user=myUser, token=token)

            if otp_instance.is_valid():
                myUser.is_active = True
                myUser.save()
                if "company/create" in next:
                    messages.success(request, "Votre compte a été activé avec succès ! Vous pouvez maintenant créer votre entreprise.")
                    # return redirect(f"/auth/company/create/{uidb64}")
                else:
                    messages.success(request, "Votre compte a été activé avec succès ! Vous pouvez vous connecter maintenant.")

                # If next parameter is provided, use it for redirection
                if next:
                    return redirect(next)

                # Otherwise, check if this is a company owner and redirect accordingly
                from account.models import Profil, UserRole
                try:
                    profile = Profil.objects.get(owner=myUser)
                    if profile.role == UserRole.COMPANY_OWNER:
                        return redirect(f"/auth/company/create/{uidb64}")
                except Profil.DoesNotExist:
                    pass

                # Default fallback
                return redirect("/auth/login")
            else:
                messages.error(request, "Le lien d'activation n'est pas valide ou a expiré.")
                return redirect("/auth/login")
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, Otp.DoesNotExist) as e:
            print(f"Activation error: {e}")
            messages.error(request, "Le lien d'activation n'est pas valide.")
            return redirect("/auth/login")

    # Handle OTP form submission (for SMS verification)
    elif request.POST:
        token = request.POST.get("token")
        print(token)
        uid = force_str(urlsafe_base64_decode(uidb64))
        print(uid)
        try:
            myUser = User.objects.get(id=int(uid))
            otp_instance = Otp.objects.get(user=myUser, token=token)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, Otp.DoesNotExist) as e:
            print(e)
            myUser = None
            otp_instance = None
        if myUser is not None and otp_instance is not None and otp_instance.is_valid():
            myUser.is_active = True
            myUser.save()
            messages.success(request, "Votre numéro de téléphone a été confirmé avec succès ! Vous pouvez vous connecter maintenant !")
            return redirect(f"/auth/login?next={ next }")
        else:
            messages.error(request, "Le token n\'est pas valide ou a expiré.")
            return redirect(f"/auth/activate?next={next}&ma={ma}&uid={uidb64}")
    else:
        return render(request, f"auth/otp.html", context={"ma": ma, "next": next, "title": "Confirmation otp", "next": next, "uid": uidb64})


def sendActivationSMS(myUser: User):
    api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))
    token = TokenGenerator.make_token()
    otp = Otp.objects.create(token=token, user=myUser)
    sms_message = SmsMessage(
        source="Serveur photo",
        body=f"{otp.token} est votre code de validation sur le serveur photo",
        to=myUser.username.removeprefix("+")
    )
    sms_messages = clicksend_client.SmsMessageCollection(messages=[sms_message])
    try:
        api_response = api_instance.sms_send_post(sms_messages)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMSApi->sms_send_post: %s\n" % e)
    return


def sendActivationEmail(myUser: User, request=None, next_url=None):
    """Send an activation email to the user."""
    token = TokenGenerator.make_token()
    otp = Otp.objects.create(token=token, user=myUser)

    # Get the current site
    if request:
        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain
    else:
        site_name = "Serveur photo"
        domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'

    # Create the email context
    uid = urlsafe_base64_encode(force_bytes(myUser.id))
    context = {
        'user': myUser,
        'first_name': myUser.first_name,
        'last_name': myUser.last_name,
        'token': token,
        'uid': uid,
        'site_name': site_name,
        'domain': domain,
        'protocol': 'https' if request and request.is_secure() else 'http',
        'request': request,
        'next': next_url or '/account',
    }

    # Render the email templates
    email_subject = "Activation de votre compte entreprise"
    email_body_html = render_to_string('auth/email_confirm.html', context)
    email_body_text = strip_tags(email_body_html)

    # Send the email
    from_email = settings.EMAIL_HOST_USER

    send_mail(
            subject=email_subject,
            message=email_body_text,
            from_email=from_email,
            recipient_list=[myUser.email],
            html_message=email_body_html,
            fail_silently=False,
        )
    # try:
    #     send_mail(
    #         subject=email_subject,
    #         message=email_body_text,
    #         from_email=from_email,
    #         recipient_list=[myUser.email],
    #         html_message=email_body_html,
    #         fail_silently=False,
    #     )
    #     return True
    # except Exception as e:
    #     print(f"Error sending activation email: {e}")
    #     return False


def new_password(request: WSGIRequest, uidb64):
    next = request.GET.get("next")
    if not request.POST:
        return render(request, "auth/new_password.html", context={"title": "Nouveau mot de passe", "next": next, "uid": uidb64})
    else:
        password = request.POST.get("password")
        password1 = request.POST.get("password1")
        if password != password1:
            messages.error(request, "Mot de passe non correspondant !")
            return redirect(f"/auth/new_password/{uidb64}" if next is None else f"/auth/new_password/{uidb64}?next={ next }")
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=int(uid))
        user.set_password(password)
        user.save()
        messages.success(request, "Votre mot de passe a été rénitialisé avec succès; Vous pouvez vous connecter !")
        return redirect("/auth/login" if next is None else f"/auth/login?next={ next }")


def reset(request: WSGIRequest):
    """
    Vue pour gérer la demande de réinitialisation de mot de passe.
    Vérifie le numéro de téléphone pour les utilisateurs classiques et
    l'adresse email pour les utilisateurs d'entreprise.
    """
    next = request.GET.get("next")

    if request.method == 'POST':
        # Récupérer l'identifiant fourni (email ou téléphone)
        identifier = request.POST.get("identifier")

        # Vérifier si l'identifiant est un email
        is_email = '@' in identifier

        if is_email:
            # Chercher l'utilisateur par email
            user = User.objects.filter(email=identifier).first()
            if not user:
                messages.error(request, "Aucun compte n'est associé à cette adresse email.")
                return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")

            # Vérifier si c'est un utilisateur d'entreprise
            try:
                profile = Profil.objects.get(owner=user)
                if profile.role != UserRole.COMPANY_OWNER:
                    messages.error(request, "Les utilisateurs d'entreprise doivent utiliser leur adresse email pour réinitialiser leur mot de passe.")
                    return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")
            except Profil.DoesNotExist:
                messages.error(request, "Profil utilisateur non trouvé.")
                return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")

            # Envoyer un email de réinitialisation
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = TokenGenerator.make_token()
            otp = Otp.objects.create(token=token, user=user)

            # Préparer le contexte pour l'email
            current_site = get_current_site(request)
            context = {
                'user': user,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'token': token,
                'uid': uid,
                'domain': current_site.domain,
                'protocol': 'https' if request.is_secure() else 'http',
                'request': request,
                'next': next,
            }

            # Envoyer l'email
            email_subject = "Réinitialisation de mot de passe"
            email_body_html = render_to_string('auth/password_reset_email.html', context)
            email_body_text = strip_tags(email_body_html)

            send_mail(
                subject=email_subject,
                message=email_body_text,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                html_message=email_body_html,
                fail_silently=False,
            )

            messages.success(request, "Un email de réinitialisation a été envoyé à votre adresse email.")
            return redirect("/auth/login" if next is None else f"/auth/login?next={next}")

        else:
            # Chercher l'utilisateur par numéro de téléphone (username)
            user = User.objects.filter(username=identifier).first()
            if not user:
                messages.error(request, "Aucun compte n'est associé à ce numéro de téléphone.")
                return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")

            # Vérifier si c'est un utilisateur classique
            try:
                profile = Profil.objects.get(owner=user)
                if profile.role != UserRole.REGULAR:
                    messages.error(request, "Les utilisateurs classiques doivent utiliser leur numéro de téléphone pour réinitialiser leur mot de passe.")
                    return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")
            except Profil.DoesNotExist:
                messages.error(request, "Profil utilisateur non trouvé.")
                return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")

            # Envoyer un SMS de réinitialisation
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = TokenGenerator.make_token()
            otp = Otp.objects.create(token=token, user=user)

            # Envoyer le SMS
            api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))
            sms_message = SmsMessage(
                source="Serveur photo",
                body=f"{otp.token} est votre code de réinitialisation de mot de passe sur le serveur photo",
                to=user.username.removeprefix("+")
            )
            sms_messages = clicksend_client.SmsMessageCollection(messages=[sms_message])
            try:
                api_response = api_instance.sms_send_post(sms_messages)
                print(api_response)
            except ApiException as e:
                print("Exception when calling SMSApi->sms_send_post: %s\n" % e)
                messages.error(request, "Une erreur s'est produite lors de l'envoi du SMS.")
                return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")

            # Rediriger vers la page de vérification du code
            return redirect(f"/auth/verify_reset_code/{uid}" if next is None else f"/auth/verify_reset_code/{uid}?next={next}")

    # Afficher le formulaire de réinitialisation
    return render(request, "auth/reset_password.html", context={"title": "Mot de passe oublié", "next": next})


def verify_reset_code(request: WSGIRequest, uidb64):
    """
    Vue pour vérifier le code de réinitialisation envoyé par SMS.
    """
    next = request.GET.get("next")

    if request.method == 'POST':
        token = request.POST.get("token")

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=int(uid))
            otp_instance = Otp.objects.get(user=user, token=token)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, Otp.DoesNotExist) as e:
            print(e)
            user = None
            otp_instance = None

        if user is not None and otp_instance is not None and otp_instance.is_valid():
            # Rediriger vers la page de définition du nouveau mot de passe
            return redirect(f"/auth/new_password/{uidb64}" if next is None else f"/auth/new_password/{uidb64}?next={next}")
        else:
            messages.error(request, "Le code n'est pas valide ou a expiré.")
            return redirect(f"/auth/verify_reset_code/{uidb64}" if next is None else f"/auth/verify_reset_code/{uidb64}?next={next}")

    return render(request, "auth/verify_reset_code.html", context={"title": "Vérification du code", "next": next, "uid": uidb64})


def reset_pwd(request: WSGIRequest, uidb64, token):
    next = request.GET.get("next")
    if not request.POST:
        uid = force_str(urlsafe_base64_decode(uidb64))
        try:
            myUser =  User.objects.get(id=int(uid))
            otp_instance = Otp.objects.get(user=myUser, token=token)

            if otp_instance.is_valid():
                messages.success(request, "Renseignez votre nouveau mot de passe !")
                return redirect(f"/auth/new_password/{uidb64}" if next is None else f"/auth/new_password/{uidb64}?next={next}")
            else:
                messages.error(request, "Le lien de réinitialisation n'est pas valide ou a expiré.")
                return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, Otp.DoesNotExist):
            messages.error(request, "Le lien de réinitialisation n'est pas valide.")
            return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")

    return redirect("/auth/reset" if next is None else f"/auth/reset?next={next}")


def company_register(request: WSGIRequest):
    """View for registering company owners and their companies in one step."""
    if request.user.is_authenticated:
        return redirect("/account")

    next = request.GET.get("next")

    if request.method == 'POST':
        form = CombinedCompanyRegistrationForm(request.POST)
        if form.is_valid():
            # Save both user and company in one step
            user = form.save()

            uid = urlsafe_base64_encode(force_bytes(user.id))

            messages.success(request, "Votre compte et votre entreprise ont été créés avec succès ! Nous vous avons envoyé un email d'activation")

            # Send activation email
            sendActivationEmail(user, request, None)

            # Redirect to a confirmation page
            return redirect(f"/auth/login?email_sent=true")
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CombinedCompanyRegistrationForm()

    return render(request, "auth/company_register.html", context={
        "title": "Création de compte entreprise",
        "next": next,
        "form": form
    })


def company_create(request: WSGIRequest, uid):
    """View for creating a company after user registration."""
    next = request.GET.get("next")

    # Decode user ID
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(id=int(user_id))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "Utilisateur invalide.")
        return redirect("/auth/login")

    # Check if user is active
    if not user.is_active:
        messages.error(request, "Veuillez d'abord activer votre compte.")
        return redirect(f"/auth/activate?next=/auth/company/create/{uid}&uid={uid}")

    if request.method == 'POST':
        form = CompanyCreationForm(request.POST)
        if form.is_valid():
            company = form.save()

            # Link company to user's profile
            from account.models import Profil
            profile = Profil.objects.get(owner=user)
            profile.company = company
            profile.save()

            messages.success(request, "Votre entreprise a été créée avec succès !")
            return redirect("/account")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CompanyCreationForm()

    return render(request, "auth/company_create.html", context={
        "title": "Création d'entreprise",
        "next": next,
        "form": form,
        "uid": uid
    })
