import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.table import WD_TABLE_ALIGNMENT


# ── Colour palette ──────────────────────────────────────────
BLUE_DARK  = RGBColor(31,  73,  125)   # name heading
BLUE_MID   = RGBColor(68,  114, 196)   # section headings
GREY_MED   = RGBColor(89,  89,  89)    # company, school
GREY_LIGHT = RGBColor(127, 127, 127)   # dates
BLACK      = RGBColor(0,   0,   0)     # body text


def _set_font(run, size: float, bold: bool = False,
              italic: bool = False, color: RGBColor = None):
    run.font.size    = Pt(size)
    run.font.bold    = bold
    run.font.italic  = italic
    run.font.color.rgb = color or BLACK
    run.font.name    = "Calibri"


def _para_spacing(p, before: float = 0, after: float = 0, line: float = None):
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after  = Pt(after)
    if line:
        from docx.shared import Pt as _Pt
        p.paragraph_format.line_spacing = _Pt(line)


def _section_heading(doc: Document, title: str):
    """Blue bold heading with a full-width underline rule."""
    p = doc.add_paragraph()
    _para_spacing(p, before=6, after=1)
    run = p.add_run(title.upper())
    _set_font(run, 10, bold=True, color=BLUE_MID)

    # Underline rule via paragraph border
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "4")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "4472C4")
    pBdr.append(bot)
    pPr.append(pBdr)


def _add_tab_stop_right(p, position_inches: float):
    """Add a right-aligned tab stop so dates flush-right."""
    from docx.oxml import OxmlElement
    from docx.shared import Inches
    pPr  = p._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    tab  = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:pos"), str(int(position_inches * 1440)))  # twips
    tabs.append(tab)
    pPr.append(tabs)


def generate_word_resume(resume_data: dict, output_path: str = "output") -> str:
    """Generate a clean, well-formatted Word resume from tailored resume data."""
    os.makedirs(output_path, exist_ok=True)

    doc = Document()

    # ── Page setup ───────────────────────────────────────────
    for sec in doc.sections:
        sec.top_margin    = Inches(0.5)
        sec.bottom_margin = Inches(0.5)
        sec.left_margin   = Inches(0.6)
        sec.right_margin  = Inches(0.6)

    # Set default paragraph font
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    # ── Name ─────────────────────────────────────────────────
    name = (resume_data.get("name") or "Your Name").strip()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _para_spacing(p, before=0, after=1)
    run = p.add_run(name)
    _set_font(run, 18, bold=True, color=BLUE_DARK)

    # ── Contact line ─────────────────────────────────────────
    contact = resume_data.get("contact") or {}
    parts = [
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("location", ""),
        contact.get("linkedin", ""),
    ]
    contact_line = "   |   ".join(x.strip() for x in parts if x and x.strip())
    if contact_line:
        cp = doc.add_paragraph(contact_line)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _para_spacing(cp, before=0, after=4)
        for run in cp.runs:
            _set_font(run, 8.5, color=GREY_MED)

    # ── Professional Summary ──────────────────────────────────
    summary = (resume_data.get("summary") or "").strip()
    if summary:
        _section_heading(doc, "Professional Summary")
        sp = doc.add_paragraph(summary)
        _para_spacing(sp, before=2, after=1)
        for run in sp.runs:
            _set_font(run, 10)

    # ── Core Skills (3-column grid) ───────────────────────────
    skills = [s.strip() for s in (resume_data.get("skills") or []) if s and s.strip()]
    if skills:
        _section_heading(doc, "Core Skills")
        cols = 3
        rows = [skills[i:i+cols] for i in range(0, len(skills), cols)]
        tbl = doc.add_table(rows=len(rows), cols=cols)
        tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
        tbl.style = "Table Grid"

        # Remove all borders for a clean look
        tbl_el = tbl._tbl
        tblPr  = tbl_el.find(qn("w:tblPr"))
        if tblPr is None:
            tblPr = OxmlElement("w:tblPr")
            tbl_el.insert(0, tblPr)
        tblBorders = OxmlElement("w:tblBorders")
        for side in ("top","left","bottom","right","insideH","insideV"):
            el = OxmlElement(f"w:{side}")
            el.set(qn("w:val"), "none")
            tblBorders.append(el)
        tblPr.append(tblBorders)

        for r_idx, row_data in enumerate(rows):
            row = tbl.rows[r_idx]
            for c_idx, skill in enumerate(row_data):
                cell = row.cells[c_idx]
                cell.text = ""
                p = cell.paragraphs[0]
                _para_spacing(p, before=1, after=1)
                run = p.add_run(f"• {skill}")
                _set_font(run, 10)

        doc.add_paragraph()  # spacer after table

    # ── Professional Experience ───────────────────────────────
    experience = resume_data.get("experience") or []
    if experience:
        _section_heading(doc, "Professional Experience")

        # Page width minus margins for tab stop
        tab_pos = 6.3  # inches (approx usable width)

        for job in experience:
            title   = (job.get("title")   or "").strip()
            company = (job.get("company") or "").strip()
            dates   = (job.get("dates")   or "").strip()
            bullets = job.get("bullets")  or []

            # Title — Company                              Dates (right-aligned)
            p = doc.add_paragraph()
            _para_spacing(p, before=5, after=1)
            _add_tab_stop_right(p, tab_pos)

            title_run = p.add_run(title)
            _set_font(title_run, 11, bold=True)

            if company:
                sep_run = p.add_run("  |  ")
                _set_font(sep_run, 10, color=GREY_MED)
                co_run = p.add_run(company)
                _set_font(co_run, 10, color=GREY_MED)

            if dates:
                tab_run = p.add_run(f"\t{dates}")
                _set_font(tab_run, 9, italic=True, color=GREY_LIGHT)

            # Bullet points
            for bullet in bullets:
                bullet = bullet.strip()
                if not bullet:
                    continue
                # Strip leading bullet chars if GPT added them
                if bullet.startswith(("•", "-", "*")):
                    bullet = bullet[1:].strip()
                bp = doc.add_paragraph(style="List Bullet")
                bp.paragraph_format.left_indent   = Inches(0.15)
                bp.paragraph_format.first_line_indent = Inches(-0.15)
                _para_spacing(bp, before=0, after=1)
                run = bp.add_run(bullet)
                _set_font(run, 10)

    # ── Education ─────────────────────────────────────────────
    education = resume_data.get("education") or []
    if education:
        _section_heading(doc, "Education")
        tab_pos = 6.3
        for edu in education:
            degree = (edu.get("degree") or "").strip()
            school = (edu.get("school") or "").strip()
            year   = (edu.get("year")   or "").strip()

            p = doc.add_paragraph()
            _para_spacing(p, before=3, after=1)
            _add_tab_stop_right(p, tab_pos)

            deg_run = p.add_run(degree)
            _set_font(deg_run, 10, bold=True)

            if school:
                sep = p.add_run("  |  ")
                _set_font(sep, 10, color=GREY_MED)
                sch = p.add_run(school)
                _set_font(sch, 10, color=GREY_MED)

            if year:
                yr = p.add_run(f"\t{year}")
                _set_font(yr, 9, italic=True, color=GREY_LIGHT)

    # ── Certifications (2-column layout) ─────────────────────
    certs = [c.strip() for c in (resume_data.get("certifications") or []) if c and c.strip()]
    if certs:
        _section_heading(doc, "Certifications")
        # Pad to even number for 2 columns
        if len(certs) % 2 != 0:
            certs.append("")
        rows = [certs[i:i+2] for i in range(0, len(certs), 2)]
        tbl = doc.add_table(rows=len(rows), cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
        tbl.style = "Table Grid"
        # Remove borders
        tbl_el = tbl._tbl
        tblPr  = tbl_el.find(qn("w:tblPr"))
        if tblPr is None:
            tblPr = OxmlElement("w:tblPr")
            tbl_el.insert(0, tblPr)
        tblBorders = OxmlElement("w:tblBorders")
        for side in ("top","left","bottom","right","insideH","insideV"):
            el = OxmlElement(f"w:{side}")
            el.set(qn("w:val"), "none")
            tblBorders.append(el)
        tblPr.append(tblBorders)
        for r_idx, row_data in enumerate(rows):
            row = tbl.rows[r_idx]
            for c_idx, cert in enumerate(row_data):
                cell = row.cells[c_idx]
                cell.text = ""
                p = cell.paragraphs[0]
                _para_spacing(p, before=1, after=1)
                run = p.add_run(f"• {cert}" if cert else "")
                _set_font(run, 10)
        doc.add_paragraph()

    # ── Projects ──────────────────────────────────────────────
    projects = resume_data.get("projects") or []
    projects = [pr for pr in projects if pr.get("name", "").strip()]
    if projects:
        _section_heading(doc, "Projects")
        for proj in projects:
            pname = (proj.get("name")        or "").strip()
            desc  = (proj.get("description") or "").strip()
            p = doc.add_paragraph()
            _para_spacing(p, before=4, after=1)
            name_run = p.add_run(pname)
            _set_font(name_run, 10, bold=True)
            if desc:
                desc_run = p.add_run(f":  {desc}")
                _set_font(desc_run, 10)

    # ── Save ──────────────────────────────────────────────────
    safe_name = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
    filename  = f"{safe_name}_Resume.docx"
    filepath  = os.path.join(output_path, filename)
    doc.save(filepath)
    return filepath
