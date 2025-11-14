from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=100)
    tags = models.CharField(max_length=100)
    description = models.TextField()
    video_file = models.FileField(upload_to='Emotisement/%y')

    def __str__(self):
        return self.title


class VideoEmotions(models.Model):
    video = models.ForeignKey('Video', on_delete=models.CASCADE)
    emotions_and_timestamp = models.JSONField(null=True)

    def __str__(self):
        return f"Emotions for {self.video.id}"

class VideoReport(models.Model):
    video = models.ForeignKey('Video', on_delete=models.CASCADE)
    report = models.JSONField(null=True)

    def __str__(self):
        return f"Report for {self.video.id}"
