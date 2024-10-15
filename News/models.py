from django.db import models

# Create your models here.
class News(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=200)
    text = models.TextField(max_length=200)
    author = models.CharField(max_length=100)
    published_date = models.DateField()
    points = models.IntegerField(default=0) 

    def __str__(self):
        return self.title
    
class Comments(models.Model):
    text = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    News = models.ForeignKey(News, on_delete=models.CASCADE)


    def __str__(self):
        return self.text