from __future__ import annotations
from flask import abort

from ..cluster import mark_prompt
from ..tasks.video import generate_scene
from ..tasks.hunyuan import generate_scene_hunyuan
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from ..tasks.video import generate_scene
from ..extensions import db, socketio
from ..forms import PromptForm, StoryCreateForm
from ..models import Scene, Story
from flask_socketio import emit, join_room


story_bp = Blueprint("story", __name__, template_folder="../templates/story")



@story_bp.route("/stories")
@login_required
def dashboard():
    my_stories = Story.query.filter(
        (Story.creator_id == current_user.id) | (Story.scenes.any(Scene.author_id == current_user.id))
    ).all()
    return render_template("story/dashboard.html", stories=my_stories)


@story_bp.route("/stories/create", methods=["GET", "POST"])
@login_required
def create_story():
    form = StoryCreateForm()
    if form.validate_on_submit():
        story = Story(title=form.title.data.strip(), creator=current_user)
        db.session.add(story)
        db.session.commit()
        flash("Story created! Add your first scene.", "success")
        return redirect(url_for("story.view_story", story_id=story.id))
    return render_template("story/create.html", form=form)


# @story_bp.route("/story/<string:story_id>", methods=["GET", "POST"])
# @login_required
# def view_story(story_id: str):
#     story: Story | None = Story.query.get_or_404(story_id)
#     scenes = story.scenes
#     form = PromptForm()
#     if form.validate_on_submit():
#             scene = Scene(prompt=form.prompt.data.strip(), story=story, author=current_user, style=None)
#             db.session.add(scene)
#             db.session.commit()
#             # ⬇️ ➋ record “last prompt” timestamp in Firestore
#             mark_prompt()
#             if form.engine.data == "hunyuan":
#                 generate_scene_hunyuan.delay(scene.id)
#             else:
#                 generate_scene.delay(scene.id)
#             socketio.emit("scene_queued", {"story_id": story.id, "scene_id": scene.id}, to=story.id)
#             flash("Scene queued for rendering.", "info")
#             return redirect(url_for("story.view_story", story_id=story.id))
#     return render_template(
#         "story/detail.html", story=story, scenes=scenes, form=form, current_user=current_user
#     )


# Socket.IO events
@socketio.on("join")
def on_join(data):
    room = data.get("story_id")
    if room:
        join_room(room)


@story_bp.route("/story/<string:story_id>", methods=["GET", "POST"])
@login_required
def view_story(story_id: str):
    story: Story = Story.query.get_or_404(story_id)
    scenes = story.scenes
    form = PromptForm()
    current_player = story.participants[story.current_turn_idx] if story.participants else story.creator

    if form.validate_on_submit():
        if current_user != current_player:
            flash("It’s not your turn yet!", "warning")
            return redirect(request.url)
        scene = Scene(prompt=form.prompt.data.strip(), story=story, author=current_user)
        db.session.add(scene)
        db.session.commit()

        mark_prompt()
        # advance turn
        story.next_participant()
        db.session.commit()

        if form.engine.data == "hunyuan":
            generate_scene_hunyuan.delay(scene.id)
        else:
            generate_scene.delay(scene.id)
        socketio.emit("scene_queued", {"story_id": story.id, "scene_id": scene.id}, to=story.id)
        flash("Scene queued for rendering.", "info")
        return redirect(url_for("story.view_story", story_id=story.id))

    return render_template(
        "story/detail.html", story=story, scenes=scenes, form=form, current_player=current_player, current_user=current_user
    )


@story_bp.route("/story/<string:story_id>/fork/<int:scene_id>")
@login_required
def fork_story(story_id: str, scene_id: int):
    orig: Story = Story.query.get_or_404(story_id)
    scene = Scene.query.get_or_404(scene_id)
    if scene.story_id != orig.id:
        abort(404)
    new_story = Story(title=f"{orig.title} (Branch)", creator=current_user)
    db.session.add(new_story)
    db.session.flush()
    # copy scenes up to chosen scene
    for sc in orig.scenes:
        clone = Scene(
            prompt=sc.prompt,
            video_url=sc.video_url,
            thumb_url=sc.thumb_url,
            style=sc.style,
            status=sc.status,
            duration_secs=sc.duration_secs,
            story=new_story,
            author=sc.author,
        )
        db.session.add(clone)
        if sc.id == scene.id:
            break
    db.session.commit()
    flash("Branch created!", "success")
    return redirect(url_for("story.view_story", story_id=new_story.id))
