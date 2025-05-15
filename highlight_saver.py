import os
from PyQt5.QtWidgets import QFileDialog
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import logging
from typing import List
from models import Highlight

class HighlightSaver:
    def __init__(self, parent):
        self.parent = parent
        self.timebase = 60  # Premiere Pro의 프레임 속도 (60fps)

    def save_highlights(self, highlights: List[Highlight]) -> bool:
        """
        하이라이트를 텍스트 파일과 XML 마커 파일로 저장.
        :param highlights: 하이라이트 리스트
        :return: 저장 성공 여부
        """
        try:
            # 파일 저장 대화상자 열기
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, 
                "하이라이트 저장", 
                "", 
                "Text Files (*.txt);;All Files (*)"
            )
            if not file_path:
                logging.warning("파일 저장이 취소됨")
                return False

            # 파일 확장자가 .txt가 아니면 추가
            if not file_path.endswith('.txt'):
                file_path += '.txt'

            # 파일 이름 추출 (확장자 제외)
            file_name = os.path.splitext(os.path.basename(file_path))[0]

            # 텍스트 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                for h in highlights:
                    f.write(h.to_display_string() + '\n')
            logging.debug(f"텍스트 파일 저장 완료: {file_path}")

            # XML 마커 파일 생성
            xml_path = file_path.replace('.txt', '_markers.xml')
            self.save_xml_markers(highlights, xml_path, file_name)
            logging.debug(f"XML 마커 파일 저장 완료: {xml_path}")

            return True

        except Exception as e:
            logging.error(f"하이라이트 저장 중 오류: {str(e)}")
            return False

    def save_xml_markers(self, highlights: List[Highlight], xml_path: str, file_name: str):
        """
        하이라이트 데이터를 Adobe Premiere Pro 호환 XML 마커 파일로 저장.
        :param highlights: 하이라이트 리스트
        :param xml_path: 저장할 XML 파일 경로
        :param file_name: 시퀀스 이름으로 사용할 파일 이름 (확장자 제외)
        """
        try:
            # XML 루트 요소 생성
            root = Element("xmeml")
            root.set("version", "4")

            # 시퀀스 요소
            sequence = SubElement(root, "sequence")
            sequence.set("id", "sequence_1")
            sequence.set("TL.SQAudioVisibleBase", "0")
            sequence.set("TL.SQVideoVisibleBase", "0")
            sequence.set("TL.SQVisibleBaseTime", "0")
            sequence.set("TL.SQAVDividerPosition", "0.5")
            sequence.set("TL.SQHideShyTracks", "0")
            sequence.set("TL.SQHeaderWidth", "292")
            sequence.set("Monitor.ProgramZoomOut", "0")
            sequence.set("Monitor.ProgramZoomIn", "0")
            sequence.set("TL.SQTimePerPixel", "0.2")
            sequence.set("MZ.EditLine", "0")
            sequence.set("MZ.Sequence.PreviewFrameSizeHeight", "1080")
            sequence.set("MZ.Sequence.PreviewFrameSizeWidth", "1920")
            sequence.set("MZ.Sequence.AudioTimeDisplayFormat", "200")
            sequence.set("MZ.Sequence.PreviewRenderingClassID", "1061109567")
            sequence.set("MZ.Sequence.PreviewRenderingPresetCodec", "1634755439")
            sequence.set("MZ.Sequence.PreviewRenderingPresetPath", "EncoderPresets/SequencePreview/795454d9-d3c2-429d-9474-923ab13b7018/QuickTime.epr")
            sequence.set("MZ.Sequence.PreviewUseMaxRenderQuality", "false")
            sequence.set("MZ.Sequence.PreviewUseMaxBitDepth", "false")
            sequence.set("MZ.Sequence.EditingModeGUID", "795454d9-d3c2-429d-9474-923ab13b7018")
            sequence.set("MZ.Sequence.VideoTimeDisplayFormat", "101")
            sequence.set("MZ.WorkOutPoint", "4612930560000")
            sequence.set("MZ.WorkInPoint", "0")
            sequence.set("explodedTracks", "true")

            # UUID
            uuid = SubElement(sequence, "uuid")
            uuid.text = "ebff5d35-481f-4d04-9b18-56efca5fb952"

            # Duration
            duration = SubElement(sequence, "duration")
            max_duration = max((h.raw_end for h in highlights), default=107700)
            duration.text = str(int(max_duration * self.timebase))

            # Rate
            rate = SubElement(sequence, "rate")
            timebase = SubElement(rate, "timebase")
            timebase.text = str(self.timebase)
            ntsc = SubElement(rate, "ntsc")
            ntsc.text = "FALSE"

            # Name
            name = SubElement(sequence, "name")
            name.text = file_name

            # Media
            media = SubElement(sequence, "media")
            video = SubElement(media, "video")
            format_ = SubElement(video, "format")
            samplecharacteristics = SubElement(format_, "samplecharacteristics")
            format_rate = SubElement(samplecharacteristics, "rate")
            format_timebase = SubElement(format_rate, "timebase")
            format_timebase.text = str(self.timebase)
            format_ntsc = SubElement(format_rate, "ntsc")
            format_ntsc.text = "FALSE"
            codec = SubElement(samplecharacteristics, "codec")
            codec_name = SubElement(codec, "name")
            codec_name.text = "Apple ProRes 422"
            appspecificdata = SubElement(codec, "appspecificdata")
            appname = SubElement(appspecificdata, "appname")
            appname.text = "Final Cut Pro"
            appmanufacturer = SubElement(appspecificdata, "appmanufacturer")
            appmanufacturer.text = "Apple Inc."
            appversion = SubElement(appspecificdata, "appversion")
            appversion.text = "7.0"
            data = SubElement(appspecificdata, "data")
            qtcodec = SubElement(data, "qtcodec")
            codecname = SubElement(qtcodec, "codecname")
            codecname.text = "Apple ProRes 422"
            codectypename = SubElement(qtcodec, "codectypename")
            codectypename.text = "Apple ProRes 422"
            codectypecode = SubElement(qtcodec, "codectypecode")
            codectypecode.text = "apcn"
            codecvendorcode = SubElement(qtcodec, "codecvendorcode")
            codecvendorcode.text = "appl"
            spatialquality = SubElement(qtcodec, "spatialquality")
            spatialquality.text = "1024"
            temporalquality = SubElement(qtcodec, "temporalquality")
            temporalquality.text = "0"
            keyframerate = SubElement(qtcodec, "keyframerate")
            keyframerate.text = "0"
            datarate = SubElement(qtcodec, "datarate")
            datarate.text = "0"
            width = SubElement(samplecharacteristics, "width")
            width.text = "1920"
            height = SubElement(samplecharacteristics, "height")
            height.text = "1080"
            anamorphic = SubElement(samplecharacteristics, "anamorphic")
            anamorphic.text = "FALSE"
            pixelaspectratio = SubElement(samplecharacteristics, "pixelaspectratio")
            pixelaspectratio.text = "square"
            fielddominance = SubElement(samplecharacteristics, "fielddominance")
            fielddominance.text = "none"
            colordepth = SubElement(samplecharacteristics, "colordepth")
            colordepth.text = "24"

            # Track
            track = SubElement(video, "track")
            track.set("TL.SQTrackShy", "0")
            track.set("TL.SQTrackExpandedHeight", "25")
            track.set("TL.SQTrackExpanded", "0")
            track.set("MZ.TrackTargeted", "0")
            enabled = SubElement(track, "enabled")
            enabled.text = "TRUE"
            locked = SubElement(track, "locked")
            locked.text = "FALSE"
            generatoritem = SubElement(track, "generatoritem")
            generatoritem.set("id", "generatoritem_1")
            gen_name = SubElement(generatoritem, "name")
            gen_name.text = "Highlight Color Matte"
            gen_enabled = SubElement(generatoritem, "enabled")
            gen_enabled.text = "TRUE"
            gen_duration = SubElement(generatoritem, "duration")
            gen_duration.text = str(int(max_duration * self.timebase))
            gen_rate = SubElement(generatoritem, "rate")
            gen_timebase = SubElement(gen_rate, "timebase")
            gen_timebase.text = str(self.timebase)
            gen_ntsc = SubElement(gen_rate, "ntsc")
            gen_ntsc.text = "FALSE"
            gen_start = SubElement(generatoritem, "start")
            gen_start.text = "0"
            gen_end = SubElement(generatoritem, "end")
            gen_end.text = str(int(max_duration * self.timebase))
            gen_in = SubElement(generatoritem, "in")
            gen_in.text = "0"
            gen_out = SubElement(generatoritem, "out")
            gen_out.text = str(int(max_duration * self.timebase))
            alphatype = SubElement(generatoritem, "alphatype")
            alphatype.text = "none"
            effect = SubElement(generatoritem, "effect")
            effect_name = SubElement(effect, "name")
            effect_name.text = "Color"
            effect_id = SubElement(effect, "effectid")
            effect_id.text = "Color"
            effect_category = SubElement(effect, "effectcategory")
            effect_category.text = "Matte"
            effect_type = SubElement(effect, "effecttype")
            effect_type.text = "generator"
            effect_mediatype = SubElement(effect, "mediatype")
            effect_mediatype.text = "video"
            parameter = SubElement(effect, "parameter")
            parameter.set("authoringApp", "PremierePro")
            param_id = SubElement(parameter, "parameterid")
            param_id.text = "fillcolor"
            param_name = SubElement(parameter, "name")
            param_name.text = "Color"
            value = SubElement(parameter, "value")
            alpha = SubElement(value, "alpha")
            alpha.text = "0"
            red = SubElement(value, "red")
            red.text = "0"
            green = SubElement(value, "green")
            green.text = "0"
            blue = SubElement(value, "blue")
            blue.text = "0"
            filter_ = SubElement(generatoritem, "filter")
            filter_effect = SubElement(filter_, "effect")
            filter_name = SubElement(filter_effect, "name")
            filter_name.text = "Opacity"
            filter_effectid = SubElement(filter_effect, "effectid")
            filter_effectid.text = "opacity"
            filter_effectcategory = SubElement(filter_effect, "effectcategory")
            filter_effectcategory.text = "motion"
            filter_effecttype = SubElement(filter_effect, "effecttype")
            filter_effecttype.text = "motion"
            filter_mediatype = SubElement(filter_effect, "mediatype")
            filter_mediatype.text = "video"
            pproBypass = SubElement(filter_effect, "pproBypass")
            pproBypass.text = "false"
            filter_param = SubElement(filter_effect, "parameter")
            filter_param.set("authoringApp", "PremierePro")
            filter_param_id = SubElement(filter_param, "parameterid")
            filter_param_id.text = "opacity"
            filter_param_name = SubElement(filter_param, "name")
            filter_param_name.text = "opacity"
            valuemin = SubElement(filter_param, "valuemin")
            valuemin.text = "0"
            valuemax = SubElement(filter_param, "valuemax")
            valuemax.text = "100"
            filter_value = SubElement(filter_param, "value")
            filter_value.text = "0"

            # GeneratorItem 내부 마커 추가
            for h in highlights:
                marker = SubElement(generatoritem, "marker")
                comment = SubElement(marker, "comment")
                comment.text = h.memo
                name = SubElement(marker, "name")
                name.text = ""
                in_time = SubElement(marker, "in")
                in_time.text = str(int(h.raw_start * self.timebase))
                out_time = SubElement(marker, "out")
                out_time.text = str(int(h.raw_end * self.timebase))
                ppro_color = SubElement(marker, "pproColor")
                ppro_color.text = "4278255360"  # Green

            # Timecode
            timecode = SubElement(sequence, "timecode")
            timecode_rate = SubElement(timecode, "rate")
            timecode_timebase = SubElement(timecode_rate, "timebase")
            timecode_timebase.text = str(self.timebase)
            timecode_ntsc = SubElement(timecode_rate, "ntsc")
            timecode_ntsc.text = "FALSE"
            timecode_string = SubElement(timecode, "string")
            timecode_string.text = "00:00:00:00"
            timecode_frame = SubElement(timecode, "frame")
            timecode_frame.text = "0"
            timecode_displayformat = SubElement(timecode, "displayformat")
            timecode_displayformat.text = "NDF"

            # Labels
            labels = SubElement(sequence, "labels")
            label2 = SubElement(labels, "label2")
            label2.text = "Green"

            # Logging Info
            logginginfo = SubElement(sequence, "logginginfo")
            description = SubElement(logginginfo, "description")
            description.text = ""
            scene = SubElement(logginginfo, "scene")
            scene.text = ""
            shottake = SubElement(logginginfo, "shottake")
            shottake.text = ""
            lognote = SubElement(logginginfo, "lognote")
            lognote.text = ""
            good = SubElement(logginginfo, "good")
            good.text = ""
            originalvideofilename = SubElement(logginginfo, "originalvideofilename")
            originalvideofilename.text = ""
            originalaudiofilename = SubElement(logginginfo, "originalaudiofilename")
            originalaudiofilename.text = ""

            # Sequence 직속 마커 추가
            for h in highlights:
                marker = SubElement(sequence, "marker")
                comment = SubElement(marker, "comment")
                comment.text = h.memo
                name = SubElement(marker, "name")
                name.text = ""
                in_time = SubElement(marker, "in")
                in_time.text = str(int(h.raw_start * self.timebase))
                out_time = SubElement(marker, "out")
                out_time.text = str(int(h.raw_end * self.timebase))
                ppro_color = SubElement(marker, "pproColor")
                ppro_color.text = "4278255360"  # Green

            # XML을 예쁘게 포맷팅
            rough_string = tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

            # XML 파일 저장
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            logging.debug(f"XML 마커 파일 작성 완료: {xml_path}")

        except Exception as e:
            logging.error(f"XML 마커 파일 저장 중 오류: {str(e)}")
            raise