import os
import re
import tempfile
import shutil
from typing import Optional, List, Tuple

# ======================== BEGIN: ORIGINAL CONVERTER (renamed) ========================

def TimingPoint(off, command, goed, vol):
    offs = int(off)
    if command < 0:
        return f"{offs},{round(command,12)},4,1,0,{vol},0,{goed}\n"
    elif command > 0:
        return f"{offs},{round(command,12)},4,1,0,{vol},1,{goed}\n"
    # command == 0 => no line (avoid writing None)

def don(off):
    return f"256,192,{off},1,0,0:0:0:0:\n"

def ka(off):
    return f"256,192,{off},1,2,0:0:0:0:\n"

def Bdon(off):
    return f"256,192,{off},1,4,0:0:0:0:\n"

def Bka(off):
    return f"256,192,{off},1,12,0:0:0:0:\n"

def slide(last, off, big=False):
    # big=False (we map big rolls to normal rolls)
    global ChangingPoints
    ren = range(len(ChangingPoints))
    r = len(ChangingPoints)
    if r == 0:
        beats = 120.0
        scr = 1.0
    elif ChangingPoints[r-1][0] < last:
        beats = ChangingPoints[r-1][1]
        scr = ChangingPoints[r-1][2]
    else:
        beats = ChangingPoints[0][1]
        scr = ChangingPoints[0][2]
        for i in ren:
            if ChangingPoints[i][0] > last:
                beats = ChangingPoints[i-1][1]
                scr = ChangingPoints[i-1][2]
                break
            elif ChangingPoints[i][0] == last:
                beats = ChangingPoints[i][1]
                scr = ChangingPoints[i][2]
                break
    # guards already in ChangingPoints selection
    curve = 100 * (off - last) * beats * 1.4 * scr / 60000
    curin = 256 + int(curve)
    laster = int(last)
    return f"256,192,{laster},2,0,L|{curin}:192,1,{round(curve,12)}\n"

def spin(last, off):
    return f"256,192,{last},12,0,{off}\n"

def cleanlist(start:list, dat:list):
    ger = sorted(dat)
    seen = []
    sorted_list = [x for x in ger if x not in seen and not seen.append(x)]
    sorted_list.insert(0, data_s)
    return sorted_list

# ---- global state (same vars as your original) ----
audio = "audio.mp3"
title = ""
version = ""
timec = 0.0
timep = 0.0
gogo = 0
bpm = 0.0
bpm_k = 0.0
shou = 0.0
offset = 0.0
off_k = 0.0
songvol = 100
measure = 4/4
changed = False
glock = False
crop = []
delay_list=[]
delay_list1=[]
lasted = 0.0
tear = 0
scroll = 1.0
get = ""
ChangingPoints = []
data_s = []

# robust measure state
pending_measure = None
bar_shou_snapshot = None
bar_started = False
bar_bpm_start = 0.0
bar_scroll_start = 1.0
bar_gogo_start = 0
bar_songvol_start = 100

general_k = [
    "osu file format v14",
    "",
    "[General]",
    "AudioFilename: audio.mp3",
    "AudioLeadIn: 0",
    "PreviewTime: -1",
    "Countdown: 0",
    "SampleSet: Normal",
    "StackLeniency: 0.7",
    "Mode: 1",
    "LetterboxInBreaks: 0",
    "WidescreenStoryboard: 0",
    "",
    "[Editor]",
    "DistanceSpacing: 0.8",
    "BeatDivisor: 7",
    "GridSize: 32",
    "TimelineZoom: 1",
    "",
    "[Metadata]",
    "Title:",
    "TitleUnicode:",
    "Artist:",
    "ArtistUnicode:",
    "Creator:",
    "Version:",
    "Source:",
    "Tags:",
    "BeatmapID:0",
    "BeatmapSetID:-1",
    "",
    "[Difficulty]",
    "HPDrainRate:5",
    "CircleSize:5",
    "OverallDifficulty:7.5",
    "ApproachRate:5",
    "SliderMultiplier:1.4",
    "SliderTickRate:1",
    "",
    "[Events]",
    "//Background and Video events",
    "//Break Periods",
    "//Storyboard Layer 0 (Background)",
    "//Storyboard Layer 1 (Fail)",
    "//Storyboard Layer 2 (Pass)",
    "//Storyboard Layer 3 (Foreground)",
    "//Storyboard Layer 4 (Overlay)",
    "//Storyboard Sound Samples",
    ""
]
general = list(general_k)  # copy per map

def _reset_core_state():
    """Ensure every run starts with clean globals (fixes GOGO/kiai sticking)."""
    global audio, title, version, timec, timep, gogo, bpm, bpm_k, shou, offset, off_k
    global songvol, measure, changed, glock, crop, delay_list, delay_list1, lasted, tear
    global scroll, get, ChangingPoints, data_s
    global pending_measure, bar_shou_snapshot, bar_started
    global bar_bpm_start, bar_scroll_start, bar_gogo_start, bar_songvol_start
    global general

    audio = "audio.mp3"
    title = ""
    version = ""
    timec = 0.0
    timep = 0.0
    gogo = 0
    bpm = 0.0
    bpm_k = 0.0
    shou = 0.0
    offset = 0.0
    off_k = 0.0
    songvol = 100
    measure = 1.0  # safe default (avoid measure==0)
    changed = False
    glock = False
    crop = []
    delay_list = []
    delay_list1 = []
    lasted = 0.0
    tear = 0
    scroll = 1.0
    get = ""
    ChangingPoints = []
    data_s = []

    pending_measure = None
    bar_shou_snapshot = None
    bar_started = False
    bar_bpm_start = 0.0
    bar_scroll_start = 1.0
    bar_gogo_start = 0
    bar_songvol_start = 100

    general = list(general_k)

def _safe_strip(s: str) -> str:
    return s.strip() if s else ""

# =========================== filename sanitization ==============================

_ILLEGAL = r'[\\/:*?"<>|]'

def _sanitize_for_filename(s: str) -> str:
    if not s:
        return ""
    # replace disallowed characters with a middle dot
    s = re.sub(_ILLEGAL, "·", s)
    # collapse repeated spaces/dots
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ============================= CORE CONVERTER ==================================

def _core_convertio(filein, artist, creator, fileout):
    _reset_core_state()  # avoid kiai at map start
    global title, general, data_s, ChangingPoints, crop, delay_list, delay_list1, get, timec, scroll, version, bpm_k, glock, timep, lasted, tear, bpm, shou, offset, off_k, changed, measure, songvol, gogo
    global pending_measure, bar_shou_snapshot, bar_started
    artist = artist
    creator = creator
    with open(filein, encoding="cp932", errors='ignore')as inp:
        data = []
        data_k = []
        humen = []
        block = []
        line = inp.readline()
        while line:
            # -------- header scan to #START --------
            while _safe_strip(line) != "#START":
                if ":" in line:
                    block = line.split(":", 1)
                    key = block[0]
                    val = block[1] if len(block) > 1 else ""
                    if key == "TITLE":
                        title = val.rstrip()
                    elif key == "BPM":
                        try:
                            bpm = float(val.rstrip())
                            if bpm <= 0:
                                bpm = 120.0
                        except:
                            bpm = 120.0
                        bpm_k = bpm
                        shou = 60000/bpm*4
                        timec = float(60000/bpm)
                        timep = timec
                    elif key == "OFFSET":
                        try:
                            offset = -1000 * float(val.rstrip())
                        except:
                            offset = 0.0
                        off_k = offset
                    elif key == "SONGVOL":
                        try:
                            songvol = int(val.rstrip())
                        except:
                            songvol = 100
                    elif key == "COURSE":
                        vv = val.rstrip()
                        if vv == "Easy" or vv == "0":
                            version = "Kantan"
                        elif vv == "Normal" or vv == "1":
                            version = "Futsuu"
                        elif vv == "Hard" or vv == "2":
                            version = "Muzukashii"
                        elif vv == "Oni" or vv == "3":
                            version = "Oni"
                        elif vv == "Edit" or vv == "4":
                            version = "Inner Oni"
                        else:
                            version = vv
                line = inp.readline()
                if line == "":
                    break
            if line == "":
                break
            # ---------------------------------------
            ChangingPoints.append([offset, bpm if bpm>0 else 120.0, scroll if scroll!=0 else 1.0])
            line = inp.readline()

            if bpm <= 0:
                bpm = bpm_k if bpm_k > 0 else 120.0

            timec = 60000.0 / bpm
            timep = timec
            shou = timec * 4 * (measure if measure > 0 else 1.0)

            base_bpm = bpm if bpm > 0 else (bpm_k if bpm_k > 0 else 120.0)
            base_mpb = 60000.0 / base_bpm
            data_s = [offset, base_mpb, gogo, songvol] 

            # ---------------- main body until #END ----------------
            while _safe_strip(line) != "#END" and line != "":
                ls = _safe_strip(line)
                if ls.startswith("#"):
                    block = ls.split(" ")
                    code = block[0]
                    if code == "#BPMCHANGE":
                        if changed:
                            data_k.append([get.rstrip(","), offset, timep, gogo, songvol, bpm if bpm>0 else 120.0, scroll if scroll!=0 else 1.0])
                            changed = False
                        else:
                            changed = True
                        glock = True
                        try:
                            nbpm = float(block[1])
                            bpm = nbpm if nbpm > 0 else (bpm_k if bpm_k > 0 else 120.0)
                        except:
                            bpm = bpm_k if bpm_k > 0 else 120.0
                        timep = float(60000/bpm)
                        shou = (60000/bpm) * 4 * (measure if measure>0 else 1.0)
                    elif code == "#GOGOSTART":
                        glock = True
                        gogo = 1
                    elif code == "#GOGOEND":
                        glock = True
                        gogo = 0
                    elif code == "#MEASURE":
                        try:
                            got = block[1].split("/")
                            den = int(got[1])
                            num = int(got[0])
                            if den == 0:
                                raise ZeroDivisionError
                            new_measure = num/den
                            if new_measure <= 0:
                                new_measure = 1.0
                            if bar_started and (get != "" and not get.endswith(",")):
                                pending_measure = new_measure
                            else:
                                measure = new_measure
                                shou = (60000/(bpm if bpm>0 else 120.0)) * 4 * measure
                        except:
                            new_measure = 1.0
                            if bar_started and (get != "" and not get.endswith(",")):
                                pending_measure = new_measure
                            else:
                                measure = new_measure
                                shou = (60000/(bpm if bpm>0 else 120.0)) * 4 * measure
                    elif code == "#SCROLL":
                        if changed:
                            data_k.append([get.rstrip(","), offset, timep, gogo, songvol, bpm if bpm>0 else 120.0, scroll if scroll!=0 else 1.0])
                            changed = False
                        else:
                            changed = True
                        glock = True
                        try:
                            scr = float(block[1])
                            scroll = scr if scr != 0.0 else 1.0
                        except:
                            scroll = 1.0
                        timep = -1 * 100 / (scroll if scroll != 0.0 else 1.0)
                    elif code == "#DELAY":
                        try:
                            delay_amt = 1000*float(block[1])
                        except:
                            delay_amt = 0.0
                        delay_list.append(int(offset))
                        delay_list1.append(delay_amt)
                        offset += delay_amt
                elif not ls.startswith("//"):
                    if glock:
                        data_k.append([get.rstrip(","), offset, timep, gogo, songvol, bpm if bpm>0 else 120.0, scroll if scroll!=0 else 1.0])
                        changed = False
                        glock = False
                    if line.rstrip("\n") == ",":
                        line = "0,"
                    if get == "":
                        # bar snapshot
                        bar_shou_snapshot = shou
                        bar_bpm_start = bpm if bpm>0 else 120.0
                        bar_scroll_start = scroll if scroll!=0 else 1.0
                        bar_gogo_start = gogo
                        bar_songvol_start = songvol
                        bar_started = True
                    get += line.rstrip("\n")
                    if get.endswith(","):
                        tem = len(get.rstrip(","))
                        if tem == 0:
                            # empty bar (after branch filtering) → skip safely
                            delay_list.clear()
                            delay_list1.clear()
                            get = ""
                            data_k = []
                            bar_started = False
                            bar_bpm_start = 0.0
                            bar_scroll_start = 1.0
                            bar_gogo_start = 0
                            bar_songvol_start = 100
                            bar_shou_snapshot = None
                            if pending_measure is not None:
                                measure = pending_measure if pending_measure>0 else 1.0
                                shou = (60000/(bpm if bpm>0 else 120.0)) * 4 * measure
                                pending_measure = None
                            line = inp.readline()
                            continue

                        events = []
                        for ev in data_k:
                            idx = len(ev[0])
                            events.append((idx, ev[2], ev[3], ev[4], ev[5], ev[6]))
                        events.sort(key=lambda x: x[0])

                        yerd = offset
                        cur_bpm = bar_bpm_start if bar_bpm_start > 0 else (bpm if bpm > 0 else 120.0)
                        cur_scroll = bar_scroll_start if bar_scroll_start != 0 else 1.0
                        cur_gogo = bar_gogo_start
                        cur_songvol = bar_songvol_start

                        beats_per_bar = max(1e-9, 4.0 * (measure if measure>0 else 1.0))
                        beats_per_digit = beats_per_bar / tem  # tem > 0 ensured

                        from collections import defaultdict
                        evmap = defaultdict(list)
                        for e in events:
                            evmap[e[0]].append(e)

                        if 0 in evmap:
                            for (_, timep_ev, gogo_ev, vol_ev, bpm_ev, scroll_ev) in evmap[0]:
                                data.append([yerd, timep_ev, gogo_ev, vol_ev])
                                if len(ChangingPoints) > 0 and ChangingPoints[-1][0] == yerd:
                                    ChangingPoints[:] = ChangingPoints[:-1]
                                ChangingPoints.append([yerd, bpm_ev if bpm_ev>0 else 120.0, scroll_ev if scroll_ev!=0 else 1.0])
                                if timep_ev > 0:
                                    cur_bpm = bpm_ev if bpm_ev > 0 else (cur_bpm if cur_bpm > 0 else 120.0)
                                elif timep_ev < 0:
                                    cur_scroll = scroll_ev if scroll_ev != 0 else (cur_scroll if cur_scroll != 0 else 1.0)
                                cur_gogo = gogo_ev
                                cur_songvol = vol_ev

                        for idx_d, i_char in enumerate(get.rstrip(",")):
                            if idx_d in evmap and idx_d != 0:
                                for (_, timep_ev, gogo_ev, vol_ev, bpm_ev, scroll_ev) in evmap[idx_d]:
                                    data.append([yerd, timep_ev, gogo_ev, vol_ev])
                                    if len(ChangingPoints) > 0 and ChangingPoints[-1][0] == yerd:
                                        ChangingPoints[:] = ChangingPoints[:-1]
                                    ChangingPoints.append([yerd, bpm_ev if bpm_ev>0 else 120.0, scroll_ev if scroll_ev!=0 else 1.0])
                                    if timep_ev > 0:
                                        cur_bpm = bpm_ev if bpm_ev > 0 else (cur_bpm if cur_bpm > 0 else 120.0)
                                    elif timep_ev < 0:
                                        cur_scroll = scroll_ev if scroll_ev != 0 else (cur_scroll if cur_scroll != 0 else 1.0)
                                    cur_gogo = gogo_ev
                                    cur_songvol = vol_ev

                            if int(yerd) in delay_list:
                                yerd += delay_list1[delay_list.index(int(yerd))]
                            humen.append([yerd, i_char])

                            ms_per_beat = 60000.0 / (cur_bpm if cur_bpm > 0 else 120.0)
                            yerd += beats_per_digit * ms_per_beat

                        offset = yerd

                        delay_list.clear()
                        delay_list1.clear()
                        get = ""
                        data_k = []
                        bar_started = False
                        bar_bpm_start = 0.0
                        bar_scroll_start = 1.0
                        bar_gogo_start = 0
                        bar_songvol_start = 100
                        bar_shou_snapshot = None
                        if pending_measure is not None:
                            measure = pending_measure if pending_measure>0 else 1.0
                            shou = (60000/(bpm if bpm>0 else 120.0)) * 4 * measure
                            pending_measure = None
                line = inp.readline()
            # --------------- write file for this COURSE ---------------
            data = cleanlist(data_s, data)

            # === PATCH 3: guarantee at least one uninherited timing line ===
            has_uninherited = any((row[1] if len(row) > 1 else 0) > 0 for row in data)
            if not has_uninherited:
                base_bpm = bpm if bpm > 0 else (bpm_k if bpm_k > 0 else 120.0)
                base_mpb = 60000.0 / base_bpm
                data.insert(0, [offset, base_mpb, gogo, songvol])
            # === /PATCH 3 ===

            os.makedirs(fileout, exist_ok=True)
            safe_artist  = _sanitize_for_filename(artist)
            safe_title   = _sanitize_for_filename(title)
            safe_creator = _sanitize_for_filename(creator)
            safe_version = _sanitize_for_filename(version)
            out_path = os.path.join(fileout, f"{safe_artist} - {safe_title}({safe_creator})[{safe_version}].osu")
            if os.path.exists(out_path):
                os.remove(out_path)
            with open(out_path, mode = "a+", encoding = "utf-8") as output:
                general[21] += title
                general[22] += title
                general[23] += artist
                general[24] += artist
                general[25] += creator
                general[26] += version
                for i in general:
                    output.write(i+"\n")
                general[21] = "Title:"
                general[22] = "TitleUnicode:"
                general[23] = "Artist:"
                general[24] = "ArtistUnicode:"
                general[25] = "Creator:"
                general[26] = "Version:"
                output.write("[TimingPoints]\n")
                for i in data:
                    drx = TimingPoint(i[0], i[1], i[2], i[3])
                    if drx:
                        output.write(drx)  # skip command==0
                output.write("\n\n[HitObjects]\n")
                lasted_local = 0.0
                tear_local = 0
                while humen != []:
                    i = humen.pop(0)
                    fret = ""
                    off = i[0]
                    try:
                        tare = int(i[1])
                    except:
                        continue
                    # type mapping only
                    if tare == 1:
                        fret = don(int(off))
                    elif tare == 2:
                        fret = ka(int(off))
                    elif tare == 3:
                        fret = Bdon(int(off))
                    elif tare == 4:
                        fret = Bka(int(off))
                    elif tare == 5:
                        lasted_local = off
                        tear_local = 1
                    elif tare == 6:          # big roll -> normal roll
                        lasted_local = off
                        tear_local = 1
                    elif tare in (7, 9):     # balloon -> spinner
                        lasted_local = off
                        tear_local = 2
                    elif tare == 8:
                        if tear_local == 1:
                            fret = slide(lasted_local, off, big=False)
                        elif tear_local == 2:
                            fret = spin(int(lasted_local), int(off))
                        lasted_local = 0.0
                        tear_local = 0
                    if fret != "":
                        output.write(fret)
            # continue scanning further COURSE sections
            line = inp.readline()


# ========================= END: ORIGINAL CONVERTER =========================


# ========================= WRAPPER: COURSES + BRANCHES =========================

def _read_text(path: str, encodings=("cp932","utf-8","utf-8-sig")) -> str:
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="ignore") as f:
                return f.read()
        except Exception:
            pass
    with open(path, "r", errors="ignore") as f:
        return f.read()

def _normalize_course(name: str) -> str:
    n = (name or "").strip().lower()
    if n in ("easy","0","kantan"): return "Kantan"
    if n in ("normal","1","futsuu"): return "Futsuu"
    if n in ("hard","2","muzukashii","muzukashi"): return "Muzukashii"
    if n in ("oni","3"): return "Oni"
    if n in ("edit","4","ura","ura oni","inner oni","inner"): return "Inner Oni"
    if n == "double": return "Double"
    return (name or "").strip()

def _split_into_sections(text: str) -> List[Tuple[str,str]]:
    lines = text.splitlines(keepends=True)
    sections: List[Tuple[str,str]] = []
    header_buf: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        header_buf.append(line)
        if line.rstrip() == "#START":
            body: List[str] = []
            i += 1
            while i < len(lines) and lines[i].rstrip() != "#END":
                body.append(lines[i])
                i += 1
            if i < len(lines):
                body.append(lines[i])  # include #END
            sections.append(("".join(header_buf), "".join(body)))
            header_buf = []
        i += 1
    return sections

def _get_course_from_header(header_text: str) -> Optional[str]:
    course = None
    for ln in header_text.splitlines():
        if ":" in ln and not ln.strip().startswith("#"):
            key, val = ln.split(":", 1)
            if key.strip().upper() == "COURSE":
                course = _normalize_course(val.strip())
    return course

def _get_level_from_header(header_text: str) -> Optional[int]:
    """Parse LEVEL: value from the section header (per COURSE)."""
    for ln in header_text.splitlines():
        if ":" in ln and not ln.strip().startswith("#"):
            key, val = ln.split(":", 1)
            if key.strip().upper() == "LEVEL":
                try:
                    return int(val.strip())
                except:
                    return None
    return None

def _extract_global_title(full_tja_text: str) -> Optional[str]:
    # find the first TITLE: ... outside comments
    for ln in full_tja_text.splitlines():
        s = ln.strip()
        if s.startswith("//"):
            continue
        if ":" in s:
            k, v = s.split(":", 1)
            if k.strip().upper() == "TITLE":
                return v.strip()
    return None

def _filter_branch_body(body_text: str, keep_branch: str) -> str:
    keep = keep_branch.upper()
    out_lines: List[str] = []
    in_branch = False
    take = False
    for raw in body_text.splitlines(keepends=True):
        su = raw.strip().upper()
        if su.startswith("#BRANCHSTART"):
            in_branch = True
            take = False
            continue
        if su == "#BRANCHEND":
            in_branch = False
            take = False
            continue
        if su in ("#N", "#E", "#M"):
            take = (su == f"#{keep}")
            continue
        if in_branch:
            if take:
                out_lines.append(raw)
        else:
            out_lines.append(raw)
    return "".join(out_lines)

def _write_temp_tja(header: str, body: str, suffix: str = "") -> str:
    txt = header + body
    with tempfile.NamedTemporaryFile(mode="w", delete=False,
                                     suffix=f"{suffix}.tja", encoding="cp932") as tmpf:
        tmpf.write(txt)
        return tmpf.name

def _single_osu_in(folder: str) -> List[str]:
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".osu")]

def _read_metadata_block(osu_text: str) -> dict:
    meta = {"Title":"", "Artist":"", "Creator":"", "Version":""}
    in_meta = False
    for ln in osu_text.splitlines():
        s = ln.strip()
        if s == "[Metadata]":
            in_meta = True
            continue
        if in_meta and s.startswith("[") and s.endswith("]"):
            break
        if in_meta and ":" in s:
            k, v = s.split(":", 1)
            k = k.strip()
            v = v.strip()
            if k in meta:
                meta[k] = v
    return meta

def _force_title_and_version(osu_path: str, forced_title: Optional[str],
                             forced_version: str, branch_suffix: Optional[str]) -> None:
    """Force Title to global TITLE (if present), Version to course (+ branch suffix)."""
    with open(osu_path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    lines = txt.splitlines(keepends=True)
    out: List[str] = []
    in_meta = False
    seen_title = False
    seen_version = False
    final_version = forced_version if forced_version else "Converted"
    if branch_suffix:
        final_version = f"{final_version} - {branch_suffix}"

    for ln in lines:
        s = ln.strip()
        if s == "[Metadata]":
            in_meta = True
            out.append(ln)
            continue
        if in_meta and s.startswith("[") and s.endswith("]"):
            if forced_title is not None and not seen_title:
                out.append(f"Title: {forced_title}\n")
            if not seen_version:
                out.append(f"Version: {final_version}\n")
            in_meta = False
            out.append(ln)
            continue
        if in_meta and s.startswith("Title:"):
            if forced_title is not None:
                out.append(f"Title: {forced_title}\n")
            else:
                out.append(ln)
            seen_title = True
        elif in_meta and s.startswith("Version:"):
            out.append(f"Version: {final_version}\n")
            seen_version = True
        else:
            out.append(ln)
    if in_meta:
        if forced_title is not None and not seen_title:
            out.append(f"Title: {forced_title}\n")
        if not seen_version:
            out.append(f"Version: {final_version}\n")
    with open(osu_path, "w", encoding="utf-8") as f:
        f.writelines(out)

def _enforce_artist_creator(osu_path: str, artist: str, creator: str) -> None:
    """Force Artist:/Creator: in [Metadata] to match user input."""
    with open(osu_path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    lines = txt.splitlines(keepends=True)
    out: List[str] = []
    in_meta = False
    seen_artist = False
    seen_creator = False
    for ln in lines:
        s = ln.strip()
        if s == "[Metadata]":
            in_meta = True
            out.append(ln)
            continue
        if in_meta and s.startswith("[") and s.endswith("]"):
            if not seen_artist:
                out.append(f"Artist: {artist}\n")
            if not seen_creator:
                out.append(f"Creator: {creator}\n")
            in_meta = False
            out.append(ln)
            continue
        if in_meta and s.startswith("Artist:"):
            out.append(f"Artist: {artist}\n")
            seen_artist = True
        elif in_meta and s.startswith("Creator:"):
            out.append(f"Creator: {creator}\n")
            seen_creator = True
        else:
            out.append(ln)
    if in_meta:
        if not seen_artist:
            out.append(f"Artist: {artist}\n")
        if not seen_creator:
            out.append(f"Creator: {creator}\n")
    with open(osu_path, "w", encoding="utf-8") as f:
        f.writelines(out)

def _sanitize_meta_and_move(osu_path: str, out_dir: str) -> str:
    """Rename by metadata after sanitizing filename components."""
    with open(osu_path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    meta = _read_metadata_block(txt)
    artist = _sanitize_for_filename(meta.get("Artist") or "Various")
    title  = _sanitize_for_filename(meta.get("Title")  or "Converted")
    creator= _sanitize_for_filename(meta.get("Creator") or "tja2osu")
    version= _sanitize_for_filename(meta.get("Version") or "Converted")
    new_name = f"{artist} - {title}({creator})[{version}].osu"
    new_path = os.path.join(out_dir, new_name)
    os.makedirs(out_dir, exist_ok=True)
    if os.path.abspath(osu_path) != os.path.abspath(new_path):
        if os.path.exists(new_path):
            os.remove(new_path)
        try:
            os.replace(osu_path, new_path)
        except Exception:
            shutil.copy2(osu_path, new_path)
            os.remove(osu_path)
    return new_path

# ---------- Double detection ----------
def _is_double(header_text: str, file_path: Optional[str]) -> bool:
    h = header_text.upper()
    if "STYLE:DOUBLE" in h or "COURSE:DOUBLE" in h:
        return True
    # Japanese marker commonly used for doubles
    if "双打" in header_text:
        return True
    if file_path and ("双打" in file_path or "DOUBLE" in file_path.upper()):
        return True
    return False

# ============================== PUBLIC ENTRY =====================================

def convertio(filein, artist, creator, fileout,
              allowed_versions: Optional[List[str]] = None,
              allowed_levels: Optional[List[int]] = None,
              allowed_branches: Optional[List[str]] = None,
              skip_double: bool = True,
              **kwargs) -> bool:
    """
    Section-aware wrapper with strict course + level filtering and per-section branching.
    Each pass converts into a unique temp directory, then we:
      - FORCE Title to the TJA's global TITLE,
      - FORCE Version to the chosen course name (+ branch suffix),
      - enforce Artist/Creator from user args,
      - sanitize & rename by metadata -> final output.
    """
    def _normalize_branch_list(b):
        if not b:
            return ["M"]
        out = []
        for x in b:
            if not x:
                continue
            u = x.strip().upper()
            if u in ("N","E","M"):
                out.append(u)
        return out or ["M"]

    full_text = _read_text(filein)
    global_title = _extract_global_title(full_text)

    sections = _split_into_sections(full_text)
    if not sections:
        return False

    allowed_courses = {_normalize_course(v) for v in (allowed_versions or [])} if allowed_versions else None
    allowed_lvls = set(allowed_levels or [])
    branches = _normalize_branch_list(allowed_branches)

    wrote_any = False

    for header, body in sections:
        # Skip doubles if requested
        if skip_double and _is_double(header, filein):
            continue

        course = _get_course_from_header(header)
        level  = _get_level_from_header(header)

        # additive filters: must satisfy both if provided
        if allowed_courses is not None and course not in allowed_courses:
            continue
        if allowed_lvls and (level is None or level not in allowed_lvls):
            continue

        has_branch = ("#BRANCHSTART" in body.upper())

        if not has_branch:
            tmp_tja = _write_temp_tja(header, body, suffix=".single")
            with tempfile.TemporaryDirectory() as tmp_out:
                _core_convertio(tmp_tja, artist, creator, tmp_out)
                osu_files = _single_osu_in(tmp_out)
                for p in osu_files:
                    _force_title_and_version(p, global_title, forced_version=course or "Converted", branch_suffix=None)
                    _enforce_artist_creator(p, artist, creator)
                    _sanitize_meta_and_move(p, fileout)
                    wrote_any = True
            try: os.remove(tmp_tja)
            except: pass
            continue

        # Branched course
        for b in branches:
            body_b = _filter_branch_body(body, b)
            tmp_tja = _write_temp_tja(header, body_b, suffix=f".{b}")
            with tempfile.TemporaryDirectory() as tmp_out:
                _core_convertio(tmp_tja, artist, creator, tmp_out)
                osu_files = _single_osu_in(tmp_out)
                for p in osu_files:
                    _force_title_and_version(p, global_title, forced_version=course or "Converted", branch_suffix=b)
                    _enforce_artist_creator(p, artist, creator)
                    _sanitize_meta_and_move(p, fileout)
                    wrote_any = True
            try: os.remove(tmp_tja)
            except: pass

    return wrote_any
