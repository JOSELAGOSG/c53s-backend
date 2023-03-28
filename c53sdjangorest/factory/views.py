from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Recipe
from .serializers import RecipeSerializer


@api_view(['GET'])
def recipe_list(request):
    recipes = Recipe.objects.all()
    recipes_serializer = RecipeSerializer(recipes, many=True)
    return Response(recipes_serializer.data)
