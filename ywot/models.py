from django.contrib.auth.models import User
from django.db import models
from django.http import Http404

from lib.jsonfield import DictField


class World(models.Model):
    name = models.CharField(unique=True, max_length=255, blank=True)
        # Creating this index for much faster world lookups from World.get_or_create,
        # which are very common.
        # CREATE INDEX CONCURRENTLY world_name_upper ON ywot_world(UPPER(name));
    owner = models.ForeignKey(User, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    public_readable = models.BooleanField(default=True) # Otherwise whitelist
    public_writable = models.BooleanField(default=True) # Otherwise whitelist
    properties = DictField(default={}, blank=True)
    default_char = models.CharField(max_length=1, default=' ')

    prompt = models.TextField(blank=True)

    properties = DictField(default={})
    
    @staticmethod
    def get_or_create(name):
        """Same interface as Model.get_or_create."""
        if '/' in name:
            # These are only created manually
            try:
                return (World.objects.get(name__iexact=name), False)
            except World.DoesNotExist:
                raise Http404

        # GAE worlds were case-sensitive. Until we figure out what to do about that, just return
        # the first one:
        worlds = World.objects.filter(name__iexact=name)
        if not len(worlds):
            return (World.objects.create(name=name), True)
        return (worlds[0], False)
    
    class Meta:
        ordering = ['name']
        
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        MEDIA_ROOT
        return '/' + self.name

class Tile(models.Model):
    # ROWS = 8
    # COLS = 16
    ROWS = 14
    COLS = 18
    
    LEN = ROWS*COLS
    world = models.ForeignKey(World)

    content = models.CharField(default=' '*LEN,  max_length=LEN)
    color = models.CharField(default='0'*LEN,  max_length=LEN)
    echos = models.CharField(default='0'*LEN,  max_length=LEN)
    tileY = models.IntegerField()
    tileX = models.IntegerField()
    properties = DictField(default={})

    new = models.IntegerField(default=1)

    # properties:
    # - protected (bool)
    # - cell_props[charY][charX] = {}
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.new:
            self.content=self.world.default_char * self.LEN
            self.new=0;
        super(Tile, self).save(*args, **kwargs) # Call the "real" save() method.
        # do_something_else()
    
    def set_char(self, charY, charX, char, cid):
        from helpers import control_chars_set
        if char in control_chars_set:
            # TODO: log these guys again at some point
            char = ' '
        assert len(self.content) == self.ROWS*self.COLS
        charY, charX = int(charY), int(charX)
        index = charY*self.COLS+charX
        self.content = self.content[:index] + char + self.content[index+1:]
        self.color = self.color[:index] + cid + self.color[index+1:]


        # add sid identifier 
        # if 'cell_props' not in self.properties:
        #     self.properties['cell_props'] = {}
        # if charY not in self.properties['cell_props']:
        #     self.properties['cell_props'][charY] = {}
        # if charX not in self.properties['cell_props'][charY]:
        #     self.properties['cell_props'][charY][charX] = {}
        # self.properties['cell_props'][charY][charX]['sid'] = sid
            # self.save()

        assert len(self.content) == self.ROWS*self.COLS

    class Meta:
        unique_together=[['world', 'tileY', 'tileX']]
        
class Edit(models.Model):
    user = models.ForeignKey(User, null=True)
    ip = models.IPAddressField(null=True)
    world = models.ForeignKey(World)
    time = models.DateTimeField(auto_now_add=True) # ADD INDEX:
        #CREATE INDEX CONCURRENTLY ywot_edit_time ON ywot_edit(time);
    content = models.TextField()
    
    class Meta:
        ordering = ['time']
    
class Whitelist(models.Model):
    user = models.ForeignKey(User)
    world = models.ForeignKey(World)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=[['user', 'world']]
    

class UserWorld(models.Model):
    world = models.ForeignKey(World, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)



from django.contrib import admin
admin.site.register(World)
admin.site.register(Tile)
admin.site.register(UserWorld)
admin.site.register(Edit)