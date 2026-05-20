"""
Bot Blocking Middleware for Django REST API

Blocks known malicious bots, scrapers, and crawlers from accessing API endpoints.
Allows legitimate search engine bots only on non-API routes.
"""

import re
import time
import logging
from collections import defaultdict
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─── Known malicious bot patterns ───────────────────────────────────────────────
# These User-Agent patterns are common scrapers, content stealers, or SEO bots
# that have no legitimate reason to access your API endpoints.

BLOCKED_BOT_PATTERNS = [
    # SEO / Content scrapers
    r'AhrefsBot',
    r'SemrushBot',
    r'MJ12bot',
    r'DotBot',
    r'BLEXBot',
    r'SearchmetricsBot',
    r'YandexBot',
    r'BaiduSpider',
    r'SeznamBot',
    r'MegaIndex',
    r'Screaming Frog',
    
    # Data scraping bots
    r'DataForSeoBot',
    r'GPTBot',
    r'CCBot',
    r'anthropic-ai',
    r'Claude-Web',
    r'ChatGPT-User',
    r'Google-Extended',
    r'FacebookExternalHit',
    r'Bytespider',
    r'PetalBot',
    
    # Generic scrapers
    r'HTTrack',
    r'wget',
    r'curl/\d',  # Note: blocks curl but not custom user-agents
    r'python-requests',
    r'python-urllib',
    r'Go-http-client',
    r'Java/',
    r'libwww-perl',
    r'Scrapy',
    r'HttpClient',
    r'node-fetch',
    r'axios/',
    r'got/',
    r'undici',
    r'php-curl',
    
    # Vulnerability scanners
    r'Nikto',
    r'Nmap',
    r'sqlmap',
    r'ZmEu',
    r'masscan',
    r'Nuclei',
    r'dirsearch',
    r'gobuster',
    r'wpscan',
    
    # Generic crawler patterns
    r'crawler',
    r'spider',
    r'bot[\s/;)]',  # "bot " or "bot/" or "bot;" or "bot)" 
    r'scraper',
    r'harvest',
]

# Compile patterns for performance
BLOCKED_BOT_REGEX = re.compile(
    '|'.join(BLOCKED_BOT_PATTERNS),
    re.IGNORECASE
)

# ─── Legitimate bots (allowed on public routes, NOT on API) ─────────────────────
LEGITIMATE_BOTS = [
    r'Googlebot',
    r'bingbot',
    r'Applebot',
    r'facebookexternalhit',  # For link previews
    r'Twitterbot',
    r'LinkedInBot',
    r'WhatsApp',
    r'TelegramBot',
    r'Slackbot',
    r'Discordbot',
]

LEGITIMATE_BOT_REGEX = re.compile(
    '|'.join(LEGITIMATE_BOTS),
    re.IGNORECASE
)

# ─── Suspicious request patterns ────────────────────────────────────────────────
SUSPICIOUS_PATHS = [
    r'/\.env',
    r'/\.git',
    r'/wp-admin',
    r'/wp-login',
    r'/wp-content',
    r'/phpmyadmin',
    r'/xmlrpc\.php',
    r'/administrator',
    r'/config\.php',
    r'/\.aws',
    r'/\.ssh',
]

SUSPICIOUS_PATH_REGEX = re.compile(
    '|'.join(SUSPICIOUS_PATHS),
    re.IGNORECASE
)


class BotBlockerMiddleware:
    """
    Django middleware to block malicious bots from crawling the API.
    
    Features:
    1. Blocks known malicious bot User-Agents
    2. Blocks requests with empty User-Agent
    3. Rate-limits suspicious IPs
    4. Blocks common vulnerability scanning paths
    5. Allows legitimate search engine bots on public routes only
    
    Configuration (in settings.py):
        BOT_BLOCKER_ENABLED = True/False  (default: True)
        BOT_BLOCKER_RATE_LIMIT = 60       (max requests per minute per IP, default: 120)
        BOT_BLOCKER_WHITELIST_IPS = []    (list of whitelisted IPs)
        BOT_BLOCKER_API_PREFIXES = ['/api/']  (API paths to protect)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'BOT_BLOCKER_ENABLED', True)
        self.rate_limit = getattr(settings, 'BOT_BLOCKER_RATE_LIMIT', 120)
        self.whitelist_ips = set(getattr(settings, 'BOT_BLOCKER_WHITELIST_IPS', []))
        self.api_prefixes = getattr(settings, 'BOT_BLOCKER_API_PREFIXES', ['/api/'])
        
        # In-memory rate limiting (fallback if cache not available)
        self._rate_tracker = defaultdict(list)
    
    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)
        
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        path = request.path
        
        # 1. Always allow whitelisted IPs
        if client_ip in self.whitelist_ips:
            return self.get_response(request)
        
        # 2. Block suspicious scan paths
        if SUSPICIOUS_PATH_REGEX.search(path):
            logger.warning(
                f'[BOT_BLOCKER] Blocked suspicious path: {path} | IP: {client_ip} | UA: {user_agent[:100]}'
            )
            return HttpResponse(status=404)
        
        # 3. Block empty User-Agent on API routes
        if not user_agent and self._is_api_path(path):
            logger.warning(
                f'[BOT_BLOCKER] Blocked empty UA on API: {path} | IP: {client_ip}'
            )
            return JsonResponse(
                {'detail': 'Request blocked.'},
                status=403
            )
        
        # 4. Check if it's a legitimate bot
        is_legit_bot = bool(LEGITIMATE_BOT_REGEX.search(user_agent))
        
        # 5. Block known malicious bots
        if not is_legit_bot and BLOCKED_BOT_REGEX.search(user_agent):
            logger.warning(
                f'[BOT_BLOCKER] Blocked malicious bot: {user_agent[:100]} | IP: {client_ip} | Path: {path}'
            )
            return JsonResponse(
                {'detail': 'Access denied.'},
                status=403
            )
        
        # 6. Block ALL bots (including legit ones) from API endpoints
        if is_legit_bot and self._is_api_path(path):
            logger.info(
                f'[BOT_BLOCKER] Blocked legit bot from API: {user_agent[:100]} | Path: {path}'
            )
            return JsonResponse(
                {'detail': 'API access not available for bots.'},
                status=403
            )
        
        # 7. Rate limiting on API endpoints
        if self._is_api_path(path) and self._is_rate_limited(client_ip):
            logger.warning(
                f'[BOT_BLOCKER] Rate limited: IP {client_ip} | Path: {path} | UA: {user_agent[:80]}'
            )
            return JsonResponse(
                {'detail': 'Too many requests. Please slow down.'},
                status=429,
                headers={'Retry-After': '60'}
            )
        
        response = self.get_response(request)
        
        # Add security headers
        if self._is_api_path(path) or path.startswith('/acp/'):
            response['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet, noimageindex'
        response['X-Content-Type-Options'] = 'nosniff'
        
        return response
    
    def _get_client_ip(self, request):
        """Extract real client IP, considering proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    def _is_api_path(self, path):
        """Check if the path is an API endpoint."""
        return any(path.startswith(prefix) for prefix in self.api_prefixes)
    
    def _is_rate_limited(self, ip):
        """
        Check if an IP has exceeded the rate limit.
        Uses Django cache if available, falls back to in-memory tracking.
        """
        cache_key = f'bot_blocker:rate:{ip}'
        now = time.time()
        window = 60  # 1 minute window
        
        try:
            # Try using Django cache (Redis, etc.)
            request_times = cache.get(cache_key, [])
            # Clean old entries
            request_times = [t for t in request_times if now - t < window]
            
            if len(request_times) >= self.rate_limit:
                return True
            
            request_times.append(now)
            cache.set(cache_key, request_times, timeout=window + 10)
            return False
            
        except Exception:
            # Fallback to in-memory tracking
            self._rate_tracker[ip] = [
                t for t in self._rate_tracker[ip] if now - t < window
            ]
            
            if len(self._rate_tracker[ip]) >= self.rate_limit:
                return True
            
            self._rate_tracker[ip].append(now)
            
            # Cleanup old IPs periodically (every 1000 requests)
            if len(self._rate_tracker) > 1000:
                self._cleanup_rate_tracker(now, window)
            
            return False
    
    def _cleanup_rate_tracker(self, now, window):
        """Remove expired entries from in-memory tracker."""
        expired_ips = [
            ip for ip, times in self._rate_tracker.items()
            if not times or now - max(times) > window
        ]
        for ip in expired_ips:
            del self._rate_tracker[ip]
