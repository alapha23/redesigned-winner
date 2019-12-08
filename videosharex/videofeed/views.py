from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from videofeed.models import YouTubeVideoRecommendation, YouTubeVideoRecommendationShare
from videofeed.serializers import YouTubeVideoRecommendationSerializer, YouTubeVideoRecommendationShareSerializer
from videofeed.engine import prioritize_similar_preferences


class Notifications(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        recommendations = YouTubeVideoRecommendation.objects.all().filter(poster=request.user).order_by('-created_at')

        payloads = []

        for recommendation in recommendations:
            shares = YouTubeVideoRecommendationShare.objects.filter(recommendation=recommendation)
            shared_count = len(shares) - 1

            if shared_count > 0:
                payload = {"video_id": recommendation.video, "message": recommendation.text, "shared_count": shared_count}
                payloads.append(payload)

        return Response(payloads)

class ShareRecommendation(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def payload(self, request, recommendation):
        user_shares = YouTubeVideoRecommendationShare.objects.all().filter(sharer=request.user)
        overlapping = [share for share in user_shares if share.recommendation.id == recommendation.id]

        if len(overlapping) > 0:
            shared = True
        else:
            shared = False

        return {"id": recommendation.id, "username": recommendation.poster.username, "video": recommendation.video, "text": recommendation.text, "shared": shared}

    def post(self, request, format=None):
        request.data['sharer'] = request.user.id
        serializer = YouTubeVideoRecommendationShareSerializer(data=request.data)
        if serializer.is_valid():
            share = serializer.save()
            return Response(self.payload(request, share.recommendation))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecommendYouTubeVideo(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def payload(self, request, recommendation):
        user_shares = YouTubeVideoRecommendationShare.objects.all().filter(sharer=request.user)
        overlapping = [share for share in user_shares if share.recommendation.id == recommendation.id]

        if len(overlapping) > 0:
            shared = True
        else:
            shared = False

        return {"id": recommendation.id, "username": recommendation.poster.username, "video": recommendation.video, "text": recommendation.text, "shared": shared}
    
    def get(self, request, format=None):
        _following = request.user.following.all()
        following = [f.followed for f in _following]

        shares = YouTubeVideoRecommendationShare.objects.order_by('-created_at')

        following_shares = [share for share in shares if share.sharer in following and share.recommendation.poster.id != request.user.id]
        non_redundant_shares = []

        recommendations = set()

        for following_share in following_shares:
            recommendation_id = following_share.recommendation.id

            if recommendation_id in recommendations:
                continue
            else:
                recommendations.add(recommendation_id)
                non_redundant_shares.append(following_share)

        prioritized_shares = prioritize_similar_preferences(request.user, non_redundant_shares)

        recommendations = [share.recommendation for share in prioritized_shares]
        payloads = [self.payload(request, recommendation) for recommendation in recommendations]

        return Response(payloads)

    def post(self, request, format=None):
        request.data['poster'] = request.user.id
        serializer = YouTubeVideoRecommendationSerializer(data=request.data)

        if serializer.is_valid():
            recommendation = serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        share = YouTubeVideoRecommendationShare()
        share.sharer = request.user
        share.recommendation = recommendation 
        share.save()

        share_serializer = YouTubeVideoRecommendationShareSerializer(share)
        return Response(share_serializer.data, status=status.HTTP_201_CREATED)
