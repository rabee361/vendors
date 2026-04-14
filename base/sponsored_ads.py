from django.db import transaction

from utils.email import send_ad_budget_exhausted_email
from utils.types import AdStatus

from .models import Setting, SponsoredAd, SponsoredAdClick


class SponsoredAdClickService:
    def __init__(self, request):
        self.request = request
        self.session = request.session

    def add(self, ad, source_page=''):
        source_page = (source_page or '')[:50]
        if self.request.user.is_authenticated:
            self._track_click(ad, user=self.request.user, source_page=source_page)
            return

        self._track_click(
            ad,
            visitor_token=self._get_visitor_token(),
            source_page=source_page,
        )

    def sync_to_db(self, user):
        visitor_token = self.session.session_key
        if not visitor_token:
            return

        with transaction.atomic():
            guest_clicks = list(
                SponsoredAdClick.objects.filter(visitor_token=visitor_token).select_related('ad')
            )

            for click in guest_clicks:
                existing_click = SponsoredAdClick.objects.filter(ad=click.ad, user=user).first()
                if existing_click:
                    if click.source_page and existing_click.source_page != click.source_page:
                        existing_click.source_page = click.source_page
                        existing_click.save(update_fields=['source_page'])
                    click.delete()
                    continue

                click.user = user
                click.visitor_token = None
                click.save(update_fields=['user', 'visitor_token'])

    def _get_visitor_token(self):
        if not self.session.session_key:
            self.session.save()
        return self.session.session_key

    def _track_click(self, ad, user=None, visitor_token=None, source_page=''):
        if user is None and not visitor_token:
            return

        lookup = {'ad': ad}
        if user is not None:
            lookup['user'] = user
        else:
            lookup['visitor_token'] = visitor_token

        with transaction.atomic():
            tracked_ad = SponsoredAd.objects.select_for_update().select_related(
                'tenant__user',
                'product',
            ).get(pk=ad.pk)
            click, created = SponsoredAdClick.objects.get_or_create(
                **lookup,
                defaults={'source_page': source_page},
            )

            if created:
                click_count = tracked_ad.click_records.count()
                max_clicks = SponsoredAdClickService._get_max_clicks(tracked_ad)
                if tracked_ad.status == AdStatus.ACTIVE and click_count >= max_clicks:
                    tracked_ad.status = AdStatus.INACTIVE
                    tracked_ad.save(update_fields=['status'])
                    transaction.on_commit(
                        lambda ad_id=tracked_ad.pk: self._send_budget_exhausted_email(ad_id)
                    )
            elif source_page and click.source_page != source_page:
                click.source_page = source_page
                click.save(update_fields=['source_page'])

    @staticmethod
    def _get_max_clicks(ad):
        return Setting.calculate_sponsored_ad_click_limit(ad.budget)

    @staticmethod
    def _send_budget_exhausted_email(ad_id):
        ad = SponsoredAd.objects.select_related('tenant__user', 'product').filter(pk=ad_id).first()
        if ad:
            send_ad_budget_exhausted_email(ad)