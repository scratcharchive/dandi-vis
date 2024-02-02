# Dandiset {{ dandiset_id }}

[Open in DANDI Archive](https://dandiarchive.org/dandiset/{{ dandiset_id }})

## Files

{% for file in files %}
### {{ file.nwb_file_name }}

- [Open in Neurosift]({{ file.neurosift_url }})
{% for viz in file.visualizations %}
{% if viz.status == "submitted" %}
- {{ viz.label }} (Submitted)
{% elif viz.status == "pending" %}
- {{ viz.label }} (Pending)
{% elif viz.status == "done" %}
- [{{ viz.label }}]({{ viz.figurl }})
{% else %}
- {{ viz.label }}
{% endif %}
{% endfor %}

{% endfor %}
