from typing import Dict, List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import os
import logging
from uuid import uuid4
from highlight_recorder import Highlight  # Highlight 클래스 임포트

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class HighlightSaver:
    def __init__(self, parent):
        self.parent = parent  # HighlightRecorder 인스턴스 (QFileDialog와 QMessageBox용)

    def save_highlights(self, highlights_by_match: Dict[int, List[Highlight]]) -> bool:
        """
        하이라이트를 텍스트와 XML 파일로 저장합니다.
        반환: 저장 성공 여부 (True/False)
        """
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, "메모 저장", "highlights.txt", "Text Files (*.txt)", options=options
            )
            if not file_path:
                logging.debug("Save cancelled by user")
                return False

            base = os.path.splitext(file_path)[0]

            # 텍스트 파일 저장
            self.save_highlights_to_text(base + '_memo.txt', highlights_by_match)
            
            # XML 파일 저장
            self.save_highlights_to_xml(base, highlights_by_match)

            QMessageBox.information(self.parent, "저장 완료", "모든 하이라이트가 성공적으로 저장되었습니다.")
            return True
        except PermissionError:
            logging.error("Permission error during save_highlights")
            QMessageBox.critical(self.parent, "저장 실패", "파일 쓰기 권한이 없습니다. 다른 위치에 저장해 보세요.")
            return False
        except OSError as e:
            logging.error(f"OS error during save_highlights: {str(e)}")
            QMessageBox.critical(self.parent, "저장 실패", f"파일 저장 중 오류가 발생했습니다: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during save_highlights: {str(e)}")
            QMessageBox.critical(self.parent, "저장 실패", f"예기치 않은 오류: {str(e)}")
            return False

    def save_highlights_to_text(self, file_path: str, highlights_by_match: Dict[int, List[Highlight]]):
        """하이라이트를 텍스트 파일에 저장합니다."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for m, lst in highlights_by_match.items():
                    f.write(f"=== Match {m} ===\n\n")
                    for h in lst:
                        f.write(h.to_display_string() + '\n\n')
            logging.debug(f"Text highlights saved to {file_path}")
        except PermissionError:
            logging.error(f"Permission error saving text to {file_path}")
            raise
        except OSError as e:
            logging.error(f"OS error saving text to {file_path}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error saving text to {file_path}: {str(e)}")
            raise

    def save_highlights_to_xml(self, base_path: str, highlights_by_match: Dict[int, List[Highlight]]):
        """각 매치별 하이라이트를 XML 파일에 저장합니다."""
        try:
            for m, lst in highlights_by_match.items():
                root = Element("xmeml")
                root.set("version", "4")
                sequence = SubElement(root, "sequence", {
                    "id": f"sequence_{m}",
                    "TL.SQAudioVisibleBase": "0",
                    "TL.SQVideoVisibleBase": "0",
                    "TL.SQVisibleBaseTime": "0",
                    "TL.SQAVDividerPosition": "0.5",
                    "TL.SQHideShyTracks": "0",
                    "TL.SQHeaderWidth": "292",
                    "Monitor.ProgramZoomOut": "0",
                    "Monitor.ProgramZoomIn": "0",
                    "TL.SQTimePerPixel": "0.2",
                    "MZ.EditLine": "0",
                    "MZ.Sequence.PreviewFrameSizeHeight": "1080",
                    "MZ.Sequence.PreviewFrameSizeWidth": "1920",
                    "MZ.Sequence.AudioTimeDisplayFormat": "200",
                    "MZ.Sequence.PreviewRenderingClassID": "1061109567",
                    "MZ.Sequence.PreviewRenderingPresetCodec": "1634755439",
                    "MZ.Sequence.PreviewRenderingPresetPath": "EncoderPresets/SequencePreview/795454d9-d3c2-429d-9474-923ab13b7018/QuickTime.epr",
                    "MZ.Sequence.PreviewUseMaxRenderQuality": "false",
                    "MZ.Sequence.PreviewUseMaxBitDepth": "false",
                    "MZ.Sequence.EditingModeGUID": "795454d9-d3c2-429d-9474-923ab13b7018",
                    "MZ.Sequence.VideoTimeDisplayFormat": "101",
                    "MZ.WorkOutPoint": "4612930560000",
                    "MZ.WorkInPoint": "0",
                    "explodedTracks": "true"
                })
                SubElement(sequence, "uuid").text = str(uuid4())
                max_duration = max((h.raw_end for h in lst), default=1)
                SubElement(sequence, "duration").text = str(int(max_duration * 60))
                rate = SubElement(sequence, "rate")
                SubElement(rate, "timebase").text = "60"
                SubElement(rate, "ntsc").text = "FALSE"
                SubElement(sequence, "name").text = f"Marker - (Match {m})"
                media = SubElement(sequence, "media")
                video = SubElement(media, "video")
                format_elem = SubElement(video, "format")
                samplecharacteristics = SubElement(format_elem, "samplecharacteristics")
                rate = SubElement(samplecharacteristics, "rate")
                SubElement(rate, "timebase").text = "60"
                SubElement(rate, "ntsc").text = "FALSE"
                codec = SubElement(samplecharacteristics, "codec")
                SubElement(codec, "name").text = "Apple ProRes 422"
                appspecificdata = SubElement(codec, "appspecificdata")
                SubElement(appspecificdata, "appname").text = "Final Cut Pro"
                SubElement(appspecificdata, "appmanufacturer").text = "Apple Inc."
                SubElement(appspecificdata, "appversion").text = "7.0"
                data = SubElement(appspecificdata, "data")
                qtcodec = SubElement(data, "qtcodec")
                SubElement(qtcodec, "codecname").text = "Apple ProRes 422"
                SubElement(qtcodec, "codectypename").text = "Apple ProRes 422"
                SubElement(qtcodec, "codectypecode").text = "apcn"
                SubElement(qtcodec, "codecvendorcode").text = "appl"
                SubElement(qtcodec, "spatialquality").text = "1024"
                SubElement(qtcodec, "temporalquality").text = "0"
                SubElement(qtcodec, "keyframerate").text = "0"
                SubElement(qtcodec, "datarate").text = "0"
                SubElement(samplecharacteristics, "width").text = "1920"
                SubElement(samplecharacteristics, "height").text = "1080"
                SubElement(samplecharacteristics, "anamorphic").text = "FALSE"
                SubElement(samplecharacteristics, "pixelaspectratio").text = "square"
                SubElement(samplecharacteristics, "fielddominance").text = "none"
                SubElement(samplecharacteristics, "colordepth").text = "24"
                track = SubElement(video, "track", {
                    "TL.SQTrackShy": "0",
                    "TL.SQTrackExpandedHeight": "25",
                    "TL.SQTrackExpanded": "0",
                    "MZ.TrackTargeted": "0"
                })
                SubElement(track, "enabled").text = "TRUE"
                SubElement(track, "locked").text = "FALSE"
                generatoritem = SubElement(track, "generatoritem", {"id": f"generatoritem_{m}"})
                SubElement(generatoritem, "name").text = f"Marker Color Matte (Match {m})"
                SubElement(generatoritem, "enabled").text = "TRUE"
                SubElement(generatoritem, "duration").text = str(int(max_duration * 60))
                rate = SubElement(generatoritem, "rate")
                SubElement(rate, "timebase").text = "60"
                SubElement(rate, "ntsc").text = "FALSE"
                SubElement(generatoritem, "start").text = "0"
                SubElement(generatoritem, "end").text = str(int(max_duration * 60))
                SubElement(generatoritem, "in").text = "0"
                SubElement(generatoritem, "out").text = str(int(max_duration * 60))
                SubElement(generatoritem, "alphatype").text = "none"
                effect = SubElement(generatoritem, "effect")
                SubElement(effect, "name").text = "Color"
                SubElement(effect, "effectid").text = "Color"
                SubElement(effect, "effectcategory").text = "Matte"
                SubElement(effect, "effecttype").text = "generator"
                SubElement(effect, "mediatype").text = "video"
                parameter = SubElement(effect, "parameter", {"authoringApp": "PremierePro"})
                SubElement(parameter, "parameterid").text = "fillcolor"
                SubElement(parameter, "name").text = "Color"
                value = SubElement(parameter, "value")
                SubElement(value, "alpha").text = "0"
                SubElement(value, "red").text = "0"
                SubElement(value, "green").text = "0"
                SubElement(value, "blue").text = "0"
                filter = SubElement(generatoritem, "filter")
                effect = SubElement(filter, "effect")
                SubElement(effect, "name").text = "Opacity"
                SubElement(effect, "effectid").text = "opacity"
                SubElement(effect, "effectcategory").text = "motion"
                SubElement(effect, "effecttype").text = "motion"
                SubElement(effect, "mediatype").text = "video"
                SubElement(effect, "pproBypass").text = "false"
                parameter = SubElement(effect, "parameter", {"authoringApp": "PremierePro"})
                SubElement(parameter, "parameterid").text = "opacity"
                SubElement(parameter, "name").text = "opacity"
                SubElement(parameter, "valuemin").text = "0"
                SubElement(parameter, "valuemax").text = "100"
                SubElement(parameter, "value").text = "0"
                seen_in_values = set()
                for i, h in enumerate(lst):
                    in_value = int(h.raw_start * 60)
                    out_value = int(h.raw_end * 60)
                    if in_value >= out_value:
                        out_value = in_value + 60
                    while in_value in seen_in_values:
                        in_value += 1
                        out_value += 1
                    seen_in_values.add(in_value)
                    marker = SubElement(generatoritem, "marker")
                    SubElement(marker, "comment").text = h.memo
                    SubElement(marker, "name").text = ""
                    SubElement(marker, "in").text = str(in_value)
                    SubElement(marker, "out").text = str(out_value)
                    SubElement(marker, "pproColor").text = "4294741314"
                timecode = SubElement(sequence, "timecode")
                rate = SubElement(timecode, "rate")
                SubElement(rate, "timebase").text = "60"
                SubElement(rate, "ntsc").text = "FALSE"
                SubElement(timecode, "string").text = "00:00:00:00"
                SubElement(timecode, "frame").text = "0"
                SubElement(timecode, "displayformat").text = "NDF"
                labels = SubElement(sequence, "labels")
                SubElement(labels, "label2").text = "Iris"
                logginginfo = SubElement(sequence, "logginginfo")
                SubElement(logginginfo, "description").text = ""
                SubElement(logginginfo, "scene").text = ""
                SubElement(logginginfo, "shottake").text = ""
                SubElement(logginginfo, "lognote").text = ""
                SubElement(logginginfo, "good").text = ""
                SubElement(logginginfo, "originalvideofilename").text = ""
                SubElement(logginginfo, "originalaudiofilename").text = ""
                seen_in_values.clear()
                for i, h in enumerate(lst):
                    in_value = int(h.raw_start * 60)
                    out_value = int(h.raw_end * 60)
                    if in_value >= out_value:
                        out_value = in_value + 60
                    while in_value in seen_in_values:
                        in_value += 1
                        out_value += 1
                    seen_in_values.add(in_value)
                    marker = SubElement(sequence, "marker")
                    SubElement(marker, "comment").text = h.memo
                    SubElement(marker, "name").text = ""
                    SubElement(marker, "in").text = str(in_value)
                    SubElement(marker, "out").text = str(out_value)
                    SubElement(marker, "pproColor").text = "4294741314"
                xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
                xml_path = f"{base_path}_markers_match_{m}.xml"
                with open(xml_path, "w", encoding="utf-8") as f:
                    f.write(xml_str)
                logging.debug(f"Saved XML for match {m} at {xml_path}")
        except PermissionError:
            logging.error(f"Permission error saving XML to {xml_path}")
            raise
        except OSError as e:
            logging.error(f"OS error saving XML to {xml_path}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error saving XML to {xml_path}: {str(e)}")
            raise