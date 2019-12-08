from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from videofeed.models import YouTubeVideoRecommendation, YouTubeVideoRecommendationShare
from videofeed.serializers import YouTubeVideoRecommendationSerializer, YouTubeVideoRecommendationShareSerializer


def prioritize_similar_preferences(user, shares):
    '''
    Implements a simple cosine similarity
    '''
    user_shares = [share.recommendation.id for share in YouTubeVideoRecommendationShare.objects.all().filter(sharer=user)]
    share_similarities = []

    for share in shares:
        sharer_shares = [share.recommendation.id for share in YouTubeVideoRecommendationShare.objects.all().filter(sharer=share.sharer)]
        similarity = measure_similarity(user_shares, sharer_shares)  

        share_similarities.append((share, similarity))

    _sorted = sorted(share_similarities, key=lambda tuple: tuple[1], reverse=True)
    shares = [share_similarity[0] for share_similarity in _sorted]
    return shares

def measure_similarity(user_shares, sharer_shares):
    user_set = set(user_shares)
    sharer_set = set(sharer_shares)

    total_set = user_set.union(sharer_set)
    intersection_set = user_set.intersection(sharer_set)

    return len(intersection_set) / len(total_set)
