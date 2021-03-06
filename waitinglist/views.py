from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.models import User

from account.models import SignupCode
from waitinglist.forms import WaitingListEntryForm, CohortCreate
from waitinglist.models import WaitingListEntry, Cohort, SignupCodeCohort



def list_signup(request, post_save_redirect=None):
    if request.method == "POST":
        form = WaitingListEntryForm(request.POST)
        if form.is_valid():
            form.save()
            if post_save_redirect is None:
                post_save_redirect = reverse("waitinglist_success")
            if not post_save_redirect.startswith("/"):
                post_save_redirect = reverse(post_save_redirect)
            return redirect(post_save_redirect)
    else:
        form = WaitingListEntryForm()
    ctx = {
        "form": form,
    }
    return render(request, "waitinglist/list_signup.html", ctx)


def cohort_list(request):
    
    if not request.user.is_staff:
        raise Http404()
    
    ctx = {
        "cohorts": Cohort.objects.order_by("-created")
    }
    return render(request, "cohorts/cohort_list.html", ctx)


def cohort_create(request):
    
    if not request.user.is_staff:
        raise Http404()
    
    if request.method == "POST":
        form = CohortCreate(request.POST)
        
        if form.is_valid():
            cohort = form.save()
            return redirect("waitinglist_cohort_detail", cohort.id)
    else:
        form = CohortCreate()
    
    ctx = {
        "form": form,
    }
    return render(request, "cohorts/cohort_create.html", ctx)


def cohort_detail(request, pk):
    
    if not request.user.is_staff:
        raise Http404()
    
    cohort = get_object_or_404(Cohort, pk=pk)
    
    # people who are NOT invited or on the site already
    waiting_list = WaitingListEntry.objects.exclude(
        email__in=SignupCode.objects.values("email")
    ).exclude(
        email__in=User.objects.values("email")
    )
    
    ctx = {
        "cohort": cohort,
        "waiting_list": waiting_list,
    }
    return render(request, "cohorts/cohort_detail.html", ctx)


def cohort_member_add(request, pk):
    
    if not request.user.is_staff:
        raise Http404()
    
    cohort = Cohort.objects.get(pk=pk)
    
    if "invite_next" in request.POST:
        try:
            N = int(request.POST["invite_next"])
        except ValueError:
            return redirect("waitinglist_cohort_detail", cohort.id)
        # people who are NOT invited or on the site already
        waiting_list = WaitingListEntry.objects.exclude(
            email__in=SignupCode.objects.values("email")
        ).exclude(
            email__in=User.objects.values("email")
        )
        emails = waiting_list.values_list("email", flat=True)[:N]
    else:
        email = request.POST["email"].strip()
        if email:
            emails = [email]
        else:
            emails = []
    
    for email in emails:
        if not SignupCode.objects.filter(email=email).exists():
            signup_code = SignupCode.create(email=email, max_uses=1, expiry=730)
            signup_code.save()
            SignupCodeCohort.objects.create(signup_code=signup_code, cohort=cohort)
    
    return redirect("waitinglist_cohort_detail", cohort.id)


def cohort_send_invitations(request, pk):
    
    if not request.user.is_staff:
        raise Http404()
    
    cohort = Cohort.objects.get(pk=pk)
    cohort.send_invitations()
    
    return redirect("waitinglist_cohort_detail", cohort.id)
