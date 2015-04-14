<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
          xmlns:o="urn:schemas-microsoft-com:office:office"
          xmlns:x="urn:schemas-microsoft-com:office:excel"
          xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
          xmlns:html="http://www.w3.org/TR/REC-html40">
    <DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">
        <Author>MSFUser</Author>
        <LastAuthor>MSFUser</LastAuthor>
        <Created>2012-06-18T15:46:09Z</Created>
        <Company>Medecins Sans Frontieres</Company>
        <Version>11.9999</Version>
    </DocumentProperties>
    <ExcelWorkbook xmlns="urn:schemas-microsoft-com:office:excel">
        <WindowHeight>13170</WindowHeight>
        <WindowWidth>19020</WindowWidth>
        <WindowTopX>120</WindowTopX>
        <WindowTopY>60</WindowTopY>
        <ProtectStructure>False</ProtectStructure>
        <ProtectWindows>False</ProtectWindows>
    </ExcelWorkbook>
    <Styles>
        <Style ss:ID="mainheader">
            <Alignment ss:Horizontal="Center" ss:Vertical="Center" ss:WrapText="0"/>
            <Font ss:FontName="Calibri" x:Family="Swiss" ss:Color="#000000"/>
            <Interior ss:Color="#E6E6E6" ss:Pattern="Solid"/>
            <Borders>
             <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" />
            </Borders>
        </Style>

        <Style ss:ID="poheader">
            <Alignment ss:Horizontal="Center" ss:Vertical="Center" ss:WrapText="1"/>
            <Interior ss:Color="#ffcc99" ss:Pattern="Solid"/>
            <Borders>
             <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" />
            </Borders>
        </Style>
        <Style ss:ID="header">
            <Alignment ss:Horizontal="Center" ss:Vertical="Center" ss:WrapText="1"/>
            <Interior ss:Color="#d3d3d3" ss:Pattern="Solid"/>
            <Borders>
             <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" />
            </Borders>
        </Style>

        <Style ss:ID="line">
            <Alignment ss:Horizontal="Center" ss:Vertical="Center" ss:WrapText="1"/>
            <Borders>
             <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" />
            <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" />
            </Borders>
        </Style>

        <Style ss:ID="short_date">
            <Alignment ss:Horizontal="Center" ss:Vertical="Center" ss:WrapText="1"/>
            <Borders>
             <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1"/>
            <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1"/>
            <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1"/>
            <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1"/>
            </Borders>
              <NumberFormat ss:Format="Short Date"/>
        </Style>
    </Styles>

    <ss:Worksheet ss:Name="KPI Detail">
        ## definition of the columns' size
        <% nb_of_columns = 12 %>
        <Table x:FullColumns="1" x:FullRows="1">
            <Column ss:AutoFitWidth="1" ss:Width="120" />
            <Column ss:AutoFitWidth="1" ss:Width="120" />
            <Column ss:AutoFitWidth="1" ss:Width="300" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />
            <Column ss:AutoFitWidth="1" ss:Width="80" />

            <Row>

            </Row>
            <Row></Row>
            <Row></Row>

            % for o in objects:
                <Row>
                    % for header in getHeaderLine():
                        <Cell ss:StyleID="poheader"><Data ss:Type="String">${header |x}</Data></Cell>
                    % endfor
                </Row>

            % for line in getReportLines():
                <Row>
                    % for cell in line:
                        <Cell ss:StyleID="header"><Data ss:Type="String">${cell}</Data></Cell>
                    % endfor
                </Row>
            % endfor
            % endfor
        </Table>
        <x:WorksheetOptions/>
    </ss:Worksheet>
</Workbook>