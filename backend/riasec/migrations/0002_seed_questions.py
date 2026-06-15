from django.db import migrations

QUESTIONS = [
    # Interleaved order — one from each dimension per page (6 questions × 5 pages)
    # Page 1 (orders 1-6)
    {'order': 1,  'dimension': 'R', 'text': 'I enjoy fixing or building things with my hands.'},
    {'order': 2,  'dimension': 'I', 'text': 'I enjoy solving complex problems or puzzles.'},
    {'order': 3,  'dimension': 'A', 'text': 'I enjoy drawing, painting, or designing things.'},
    {'order': 4,  'dimension': 'S', 'text': 'I enjoy helping others solve their personal problems.'},
    {'order': 5,  'dimension': 'E', 'text': 'I enjoy leading a group or project.'},
    {'order': 6,  'dimension': 'C', 'text': 'I enjoy organising files, schedules, or data.'},
    # Page 2 (orders 7-12)
    {'order': 7,  'dimension': 'R', 'text': 'I like working with tools, machines, or equipment.'},
    {'order': 8,  'dimension': 'I', 'text': 'I like reading about science, technology, or research.'},
    {'order': 9,  'dimension': 'A', 'text': 'I like writing stories, poems, or songs.'},
    {'order': 10, 'dimension': 'S', 'text': 'I like working in teams and collaborating with others.'},
    {'order': 11, 'dimension': 'E', 'text': 'I like convincing others to try a new idea.'},
    {'order': 12, 'dimension': 'C', 'text': 'I like following clear instructions and procedures.'},
    # Page 3 (orders 13-18)
    {'order': 13, 'dimension': 'R', 'text': 'I prefer outdoor activities over sitting in an office.'},
    {'order': 14, 'dimension': 'I', 'text': 'I enjoy conducting experiments or testing ideas.'},
    {'order': 15, 'dimension': 'A', 'text': 'I enjoy performing — acting, dancing, or playing music.'},
    {'order': 16, 'dimension': 'S', 'text': 'I enjoy teaching or explaining things to my peers.'},
    {'order': 17, 'dimension': 'E', 'text': 'I enjoy competitions where I can show my skills.'},
    {'order': 18, 'dimension': 'C', 'text': 'I prefer tasks where there is a right and wrong answer.'},
    # Page 4 (orders 19-24)
    {'order': 19, 'dimension': 'R', 'text': 'I enjoy physical tasks that have clear, practical results.'},
    {'order': 20, 'dimension': 'I', 'text': 'I prefer thinking through a problem carefully before acting.'},
    {'order': 21, 'dimension': 'A', 'text': 'I like coming up with original ideas rather than following rules.'},
    {'order': 22, 'dimension': 'S', 'text': "I care deeply about fairness and people's wellbeing."},
    {'order': 23, 'dimension': 'E', 'text': 'I like setting goals and working hard to achieve them.'},
    {'order': 24, 'dimension': 'C', 'text': 'I enjoy keeping records and making sure details are accurate.'},
    # Page 5 (orders 25-30)
    {'order': 25, 'dimension': 'R', 'text': 'I like learning how mechanical or electronic devices work.'},
    {'order': 26, 'dimension': 'I', 'text': 'I like asking "why" and looking for evidence-based answers.'},
    {'order': 27, 'dimension': 'A', 'text': 'I enjoy activities that let me express my feelings or imagination.'},
    {'order': 28, 'dimension': 'S', 'text': 'I like volunteering or doing community service.'},
    {'order': 29, 'dimension': 'E', 'text': 'I enjoy starting new initiatives or projects.'},
    {'order': 30, 'dimension': 'C', 'text': 'I like working in structured, predictable environments.'},
]


def seed_questions(apps, schema_editor):
    RIASECQuestion = apps.get_model('riasec', 'RIASECQuestion')
    for q in QUESTIONS:
        RIASECQuestion.objects.get_or_create(order=q['order'], defaults=q)


def unseed_questions(apps, schema_editor):
    RIASECQuestion = apps.get_model('riasec', 'RIASECQuestion')
    RIASECQuestion.objects.filter(order__in=[q['order'] for q in QUESTIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [('riasec', '0001_initial')]
    operations = [migrations.RunPython(seed_questions, unseed_questions)]
