# les imports

from datetime import date
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# les enums

class EpisodeStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


#modèles

class Host(BaseModel):
    id: int
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    bio: Optional[str] = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def name_no_special_chars(cls, value: str) -> str:
        if not all(c.isalnum() or c in " -" for c in value):
            raise ValueError("name ne doit contenir que lettres, chiffres, espaces et tirets")
        return value


class Podcast(BaseModel):
    id: int
    title: str = Field(min_length=3, max_length=150)
    host_id: int
    category: str = Field(min_length=2, max_length=50)
    description: Optional[str] = Field(default=None, max_length=1000)


class Chapter(BaseModel):
    id: int
    episode_id: int
    title: str = Field(min_length=2, max_length=100)
    start_time_seconds: int = Field(ge=0)
    end_time_seconds: int = Field(ge=0)

    @model_validator(mode="after")
    def check_chapter_times(self):
        if self.end_time_seconds <= self.start_time_seconds:
            raise ValueError("end_time_seconds doit être strictement supérieur à start_time_seconds")
        return self


class Episode(BaseModel):
    id: int
    podcast_id: int
    title: str = Field(min_length=3, max_length=150)
    duration_minutes: int = Field(ge=1, le=600)
    status: EpisodeStatus = EpisodeStatus.DRAFT
    publish_date: Optional[date] = None
    chapters: List[Chapter] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_publish_consistency(self):
        if self.status == EpisodeStatus.PUBLISHED and self.publish_date is None:
            raise ValueError("Un épisode publié doit avoir une publish_date")
        return self


class Listener(BaseModel):
    id: int
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr

    @field_validator("username")
    @classmethod
    def username_no_special_chars(cls, value: str) -> str:
        if not value.isalnum():
            raise ValueError("username ne doit contenir que des lettres et des chiffres")
        return value


class Subscription(BaseModel):
    id: int
    listener_id: int
    podcast_id: int
    start_date: date
    end_date: Optional[date] = None
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    @model_validator(mode="after")
    def check_dates_order(self):
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValueError("end_date doit être postérieure à start_date")
        return self

class HidSub(BaseModel):
        id:int
        listener_id: int
        podcast_id: int

class HidListener(BaseModel):
    id: int
    username: str = Field(min_length=3, max_length=30)


# apply & stockage


app = FastAPI()

hosts: list[Host] = [
    Host(
        id=1,
        name="Wario",
        email="wario@gold.com",
        bio="Wario time! Le podcast officiel du trésor."
    ),
    Host(
        id=2,
        name="Alice Smith",
        email="alice.smith@tech-talk.com",
        bio="Journaliste tech passionnée par les innovations IA."
    )
]

# 2. Podcasts
podcasts: List[Podcast] = [
    Podcast(
        id=1,
        title="Wario's Money Tips",
        host_id=1,
        category="Business",
        description="Comment devenir riche très rapidement."
    ),
    Podcast(
        id=2,
        title="Tech Trends Daily",
        host_id=2,
        category="Technologie",
        description="Résumé quotidien de l'actualité numérique."
    )
]

# 3. Chapters
chapters: List[Chapter] = [
    Chapter(
        id=1,
        episode_id=1,
        title="Introduction",
        start_time_seconds=0,
        end_time_seconds=120
    ),
    Chapter(
        id=2,
        episode_id=1,
        title="Conseil numéro 1",
        start_time_seconds=121,
        end_time_seconds=600
    ),
    Chapter(
        id=3,
        episode_id=2,
        title="Présentation des puces IA",
        start_time_seconds=0,
        end_time_seconds=300
    )
]

# 4. Episodes
episodes: List[Episode] = [
    Episode(
        id=1,
        podcast_id=1,
        title="Comment doubler ses pièces en 5 minutes",
        duration_minutes=25,
        status=EpisodeStatus.PUBLISHED,
        publish_date=date(2024, 1, 15),
        chapters=[chapters[0], chapters[1]]
    ),
    Episode(
        id=2,
        podcast_id=2,
        title="Le futur des GPU en 2026",
        duration_minutes=45,
        status=EpisodeStatus.PUBLISHED,
        publish_date=date(2026, 3, 10),
        chapters=[chapters[2]]
    ),
    Episode(
        id=3,
        podcast_id=1,
        title="Épisode secret à venir",
        duration_minutes=15,
        status=EpisodeStatus.DRAFT,
        publish_date=None,
        chapters=[]
    )
]

# 5. Listeners
listeners: List[Listener] = [
    Listener(
        id=1,
        username="Luigi2000",
        email="luigi@mansion.it"
    ),
    Listener(
        id=2,
        username="TechFan42",
        email="fan@technology.io"
    )
]

# 6. Subscriptions
subscriptions: List[Subscription] = [
    Subscription(
        id=1,
        listener_id=1,
        podcast_id=1,
        start_date=date(2024, 2, 1),
        end_date=None,
        status=SubscriptionStatus.ACTIVE
    ),
    Subscription(
        id=2,
        listener_id=2,
        podcast_id=2,
        start_date=date(2023, 5, 10),
        end_date=date(2024, 5, 10),
        status=SubscriptionStatus.EXPIRED
    )
]

# 
# routes spécifiques ( qui sonts placée ici parce que si non ça elles ne fonctionnent pas exemple pour les filters)
#

@app.get("/podcasts/filter")
def filter_podcasts(category: str | None = None, host_id: int | None = None):
    results = podcasts

    if category is not None:
        results = [p for p in results if p.category.lower() == category.lower()]

    if host_id is not None:
        results = [p for p in results if p.host_id == host_id]

    if (len(results) == 0):
        raise HTTPException(status_code=400, detail="Host non trouvé, essayez d'autre champs")

    return results


@app.get("/episodes/filter")
def filter_episodes(
    podcast_id: int | None = None,
    status: EpisodeStatus | None = None,
    min_duration: int | None = None,
    max_duration: int | None = None,
):
    results = episodes

    if podcast_id is not None:
        results = [e for e in results if e.podcast_id == podcast_id]

    if status is not None:
        results = [e for e in results if e.status == status]

    if min_duration is not None:
        results = [e for e in results if e.duration_minutes >= min_duration]

    if max_duration is not None:
        results = [e for e in results if e.duration_minutes <= max_duration]

    if (len(results) == 0):
            raise HTTPException(status_code=400, detail="épisode non trouvé, essayez d'autre champs")

    return results


@app.get("/podcasts/sort")
def sort_podcasts(by: str = "title", order: str = "asc"):
    valid_fields = {"title", "category", "id"}
    if by not in valid_fields:
        raise HTTPException(status_code=400, detail="Champ de tri invalide")

    reverse = order == "desc"
    return sorted(podcasts, key=lambda p: getattr(p, by), reverse=reverse)


@app.get("/episodes/sort")
def sort_episodes(by: str = "duration_minutes", order: str = "asc"):
    valid_fields = {"title", "duration_minutes", "id"}
    if by not in valid_fields:
        raise HTTPException(status_code=400, detail="Champ de tri invalide")

    reverse = order == "desc"
    return sorted(episodes, key=lambda e: getattr(e, by), reverse=reverse)


@app.get("/podcasts/paginate")
def paginate_podcasts(page: int = 1, size: int = 10):
    start = (page - 1) * size
    end = start + size
    return {
        "page": page,
        "size": size,
        "total": len(podcasts),
        "items": podcasts[start:end],
    }


@app.get("/episodes/paginate")
def paginate_episodes(page: int = 1, size: int = 10):
    start = (page - 1) * size
    end = start + size
    return {
        "page": page,
        "size": size,
        "total": len(episodes),
        "items": episodes[start:end],
    }


@app.get("/stats")
def get_stats():
    return {
        "total_hosts": len(hosts),
        "total_podcasts": len(podcasts),
        "total_episodes": len(episodes),
        "total_listeners": len(listeners),
        "total_subscriptions": len(subscriptions),
        "published_episodes": len([e for e in episodes if e.status == EpisodeStatus.PUBLISHED]),
        "active_subscriptions": len([s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE]),
    }



# routes CRUD 


@app.get("/")
def read_root():
    return {"message": "Bienvenue sur mon API de podcasts !"}


# HOSTS 
@app.get("/hosts")
def get_hosts():
    return hosts

@app.post("/hosts")
def create_host(new_host: Host):
    hosts.append(new_host)
    return new_host

@app.get("/hosts/{host_id}")
def get_host(host_id: int):
    for host in hosts:
        if host.id == host_id:
            return host
    raise HTTPException(status_code=404, detail="Host non trouvé")

@app.patch("/hosts/{host_id}")
def update_host(host_id: int, changes: dict):
    for index, host in enumerate(hosts):
        if host.id == host_id:
            updated = host.model_copy(update=changes)
            hosts[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Host non trouvé")

@app.delete("/hosts/{host_id}")
def delete_host(host_id: int):
    global hosts
    hosts = [h for h in hosts if h.id != host_id]
    return {"message": "supprimé"}


# PODCASTS 
@app.get("/podcasts")
def get_podcasts():
    return podcasts

@app.post("/podcasts")
def create_podcast(new_podcast: Podcast):
    if not any(h.id == new_podcast.host_id for h in hosts):
        raise HTTPException(status_code=404, detail="host_id ne correspond à aucun host")
    podcasts.append(new_podcast)
    return new_podcast

@app.get("/podcasts/{podcast_id}")
def get_podcast(podcast_id: int):
    for podcast in podcasts:
        if podcast.id == podcast_id:
            return podcast
    raise HTTPException(status_code=404, detail="Podcast non trouvé")

@app.patch("/podcasts/{podcast_id}")
def update_podcast(podcast_id: int, changes: dict):
    for index, podcast in enumerate(podcasts):
        if podcast.id == podcast_id:
            updated = podcast.model_copy(update=changes)
            podcasts[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Podcast non trouvé")

@app.delete("/podcasts/{podcast_id}")
def delete_podcast(podcast_id: int):
    global podcasts
    podcasts = [p for p in podcasts if p.id != podcast_id]
    return {"message": "supprimé"}


# EPISODES
@app.get("/episodes")
def get_episodes():
    return episodes

@app.post("/episodes")
def create_episode(new_episode: Episode):
    if not any(p.id == new_episode.podcast_id for p in podcasts):
        raise HTTPException(status_code=404, detail="podcast_id ne correspond à aucun podcast")
    episodes.append(new_episode)
    return new_episode

@app.get("/episodes/{episode_id}")
def get_episode(episode_id: int):
    for episode in episodes:
        if episode.id == episode_id:
            return episode
    raise HTTPException(status_code=404, detail="Episode non trouvé")

@app.patch("/episodes/{episode_id}")
def update_episode(episode_id: int, changes: dict):
    for index, episode in enumerate(episodes):
        if episode.id == episode_id:
            updated = episode.model_copy(update=changes)
            episodes[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Episode non trouvé")

@app.delete("/episodes/{episode_id}")
def delete_episode(episode_id: int):
    global episodes
    episodes = [e for e in episodes if e.id != episode_id]
    return {"message": "supprimé"}


# CHAPTERS 
@app.get("/chapters")
def get_chapters():
    return chapters

@app.post("/chapters")
def create_chapter(new_chapter: Chapter):
    if not any(e.id == new_chapter.episode_id for e in episodes):
        raise HTTPException(status_code=404, detail="episode_id ne correspond à aucun episode")
    chapters.append(new_chapter)
    return new_chapter

@app.get("/chapters/{chapter_id}")
def get_chapter(chapter_id: int):
    for chapter in chapters:
        if chapter.id == chapter_id:
            return chapter
    raise HTTPException(status_code=404, detail="Chapter non trouvé")

@app.patch("/chapters/{chapter_id}")
def update_chapter(chapter_id: int, changes: dict):
    for index, chapter in enumerate(chapters):
        if chapter.id == chapter_id:
            updated = chapter.model_copy(update=changes)
            chapters[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Chapter non trouvé")

@app.delete("/chapters/{chapter_id}")
def delete_chapter(chapter_id: int):
    global chapters
    chapters = [c for c in chapters if c.id != chapter_id]
    return {"message": "supprimé"}


# LISTENERS CRUD
@app.get("/listeners",response_model=Listener)
def get_listeners():
    return listeners

@app.post("/listeners")
def create_listener(new_listener: Listener, response_model=Listener):
    listeners.append(new_listener)
    return new_listener

@app.get("/listeners/{listener_id}",response_model=Listener)
def get_listener(listener_id: int):
    for listener in listeners:
        if listener.id == listener_id:
            return listener
    raise HTTPException(status_code=404, detail="Listener non trouvé")

@app.patch("/listeners/{listener_id}",response_model=Listener)
def update_listener(listener_id: int, changes: dict):
    for index, listener in enumerate(listeners):
        if listener.id == listener_id:
            updated = listener.model_copy(update=changes)
            listeners[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Listener non trouvé")

@app.delete("/listeners/{listener_id}", response_model=Listener)
def delete_listener(listener_id: int):
    global listeners
    listeners = [l for l in listeners if l.id != listener_id]
    return {"message": "supprimé"}


# SUBSCRIPTIONS CRUD
@app.get("/subscriptions", response_model=Subscription)
def get_subscriptions():
    return subscriptions

@app.post("/subscriptions")
def create_subscription(new_subscription: Subscription, response_model=Subscription):
    if not any(l.id == new_subscription.listener_id for l in listeners):
        raise HTTPException(status_code=404, detail="listener_id ne correspond à aucun listener")
    if not any(p.id == new_subscription.podcast_id for p in podcasts):
        raise HTTPException(status_code=404, detail="podcast_id ne correspond à aucun podcast")
    subscriptions.append(new_subscription)
    return new_subscription

@app.get("/subscriptions/{subscription_id}",response_model=Subscription)
def get_subscription(subscription_id: int):
    for subscription in subscriptions:
        if subscription.id == subscription_id:
            return subscription
    raise HTTPException(status_code=404, detail="Subscription non trouvée")

@app.patch("/subscriptions/{subscription_id}",response_model=Subscription)
def update_subscription(subscription_id: int, changes: dict):
    for index, subscription in enumerate(subscriptions):
        if subscription.id == subscription_id:
            updated = subscription.model_copy(update=changes)
            subscriptions[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Subscription non trouvée")

@app.delete("/subscriptions/{subscription_id}",response_model=Subscription)
def delete_subscription(subscription_id: int):
    global subscriptions
    subscriptions = [s for s in subscriptions if s.id != subscription_id]
    return {"message": "supprimé"}
