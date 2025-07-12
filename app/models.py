# app/models.py
"""SQLAlchemy 2-style models for StoryLoop (Phase 4)."""

from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Table  # Integer etc. already imported

import uuid
from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


# ────────────────────────────  User  ────────────────────────────
class User(db.Model, UserMixin):  # type: ignore[misc]
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    stories_created: Mapped[list["Story"]] = relationship(
        "Story", back_populates="creator", lazy="selectin"
    )

    # ── helper methods ──
    def set_password(self, password: str) -> None:
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:  # noqa: D401
        return f"<User {self.email}>"


# ────────────────────────────  Story  ────────────────────────────
story_participants = Table(
    "story_participants",
    db.metadata,
    db.Column("story_id", String(36), ForeignKey("stories.id"), primary_key=True),
    db.Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)

class Story(db.Model):
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # FKs & relationships
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    creator: Mapped["User"] = relationship("User", back_populates="stories_created")

    scenes: Mapped[list["Scene"]] = relationship(
        "Scene",
        back_populates="story",
        order_by="Scene.created_at",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Story {self.title[:20]}…>"
    
    current_turn_idx: Mapped[int] = mapped_column(Integer, default=0)

    participants: Mapped[list["User"]] = relationship("User", secondary=story_participants, lazy="selectin")

    def next_participant(self) -> "User":
        if not self.participants:
            return self.creator
        self.current_turn_idx = (self.current_turn_idx + 1) % len(self.participants)
        return self.participants[self.current_turn_idx]


# ────────────────────────────  Scene  ────────────────────────────
class Scene(db.Model):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    video_url: Mapped[Optional[str]] = mapped_column(Text)
    thumb_url: Mapped[Optional[str]] = mapped_column(Text)
    style: Mapped[Optional[str]] = mapped_column(String(50))

    status: Mapped[str] = mapped_column(
        String(20), default="queued"
    )  # queued | rendering | done | error
    duration_secs: Mapped[int] = mapped_column(Integer, default=8)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # FKs / relationships
    story_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stories.id"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    branch_parent_scene_id: Mapped[Optional[int]] = mapped_column(Integer)

    story: Mapped["Story"] = relationship("Story", back_populates="scenes")
    author: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Scene {self.id} of Story {self.story_id}>"


# ────────────────────────────  Invite  ────────────────────────────
class Invite(db.Model):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    story_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stories.id"), nullable=False
    )
    invitee_email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="contributor")
    token: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()))
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Invite {self.invitee_email} to Story {self.story_id}>"