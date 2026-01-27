from django.apps import AppConfig

class ArabConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "arab"

    def ready(self):
        from . import signals  # noqa
        try:
            import jazzmin.templatetags.jazzmin as jazzmin_tags
            from django.utils.html import mark_safe
            from django.contrib.admin.views.main import PAGE_VAR

            def fixed_jazzmin_paginator_number(change_list, i):
                """
                Generate an individual page index link in a paginated list.
                Django 6.0 fix: use mark_safe instead of format_html without args.
                """
                html_str = ""
                start = i == 1
                end = i == change_list.paginator.num_pages
                spacer = i in (".", "…")
                current_page = i == change_list.page_num

                if start:
                    link = change_list.get_query_string({PAGE_VAR: change_list.page_num - 1}) if change_list.page_num > 1 else "#"
                    html_str += """
                    <li class="page-item previous {disabled}">
                        <a class="page-link" href="{link}" data-dt-idx="0" tabindex="0">«</a>
                    </li>
                    """.format(link=link, disabled="disabled" if link == "#" else "")

                if current_page:
                    html_str += """
                    <li class="page-item active">
                        <a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">{num}</a>
                    </li>
                    """.format(num=i)
                elif spacer:
                    html_str += """
                    <li class="page-item">
                        <a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">… </a>
                    </li>
                    """
                else:
                    query_string = change_list.get_query_string({PAGE_VAR: i})
                    end_val = "end" if end else ""
                    html_str += """
                        <li class="page-item">
                        <a href="{query_string}" class="page-link {end}" data-dt-idx="3" tabindex="0">{num}</a>
                        </li>
                    """.format(num=i, query_string=query_string, end=end_val)

                if end:
                    link = change_list.get_query_string({PAGE_VAR: change_list.page_num + 1}) if change_list.page_num < i else "#"
                    html_str += """
                    <li class="page-item next {disabled}">
                        <a class="page-link" href="{link}" data-dt-idx="7" tabindex="0">»</a>
                    </li>
                    """.format(link=link, disabled="disabled" if link == "#" else "")

                return mark_safe(html_str)

            jazzmin_tags.jazzmin_paginator_number = fixed_jazzmin_paginator_number
        except (ImportError, Exception):
            pass
