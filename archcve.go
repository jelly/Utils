package main

import (
	"fmt"
	"io"
	"encoding/xml"
	"regexp"
	"archive/tar"
	"compress/gzip"
	"os"
	"strings"
	"net/http"
)

/**
 Simple pacman db wrapper. (Provided by Dave Reisner)
*/
type Package struct {
	Name, Version string
}
func newPackage(path string) Package {
	i := strings.LastIndex(path, "-")
	// ignore the pkgrel
	j := strings.LastIndex(path[:i], "-")
	ver := path[j+1 : i]
	name := path[:j]
	return Package{name, ver}
}
func getSyncDb(dbroot, name string) ([]Package, error) {
	f, err := os.Open(fmt.Sprintf("%s/sync/%s.db", dbroot, name))
	if err != nil {
		return nil, err
	}
	defer f.Close()
	gz, err := gzip.NewReader(f)
	if err != nil {
		return nil, err
	}
	tr := tar.NewReader(gz)
	pkgs := make([]Package, 0, 30)
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		} else if err != nil {
			return nil, err
		}
		if hdr.FileInfo().IsDir() {
			pkgs = append(pkgs, newPackage(hdr.Name))
		}
	}
	return pkgs, nil
}



/*
<rdf>
<item rdf:about="http://web.nvd.nist.gov/view/vuln/detail?vulnId=CVE-2013-4148">
<title>CVE-2013-4148 (qemu)</title>
<link>
http://web.nvd.nist.gov/view/vuln/detail?vulnId=CVE-2013-4148
</link>
<description>
Integer signedness error in the virtio_net_load function in hw/net/virtio-net.c in QEMU 1.x before 1.7.2 allows remote attackers to execute arbitrary code via a crafted savevm image, which triggers a buffer overflow.
</description>
<dc:date>2014-11-04T21:55:24Z</dc:date>
</item>
</rdf>
*/

type XMLItem struct {
	XMLName xml.Name `xml:"item"`
	About string   `xml:"about,attr"`
	CVEid string `xml:"title"`
	Link string `xml:"link"`
	Description string `xml:"description"`
	Date string `xml:"date"`
}

type XMLItems struct {
	XMLName xml.Name `xml:"RDF"`
	Items []XMLItem `xml:"item"`
}

func readCVE(reader io.Reader) ([]XMLItem, error) {
    var entrys XMLItems
    if err := xml.NewDecoder(reader).Decode(&entrys); err != nil {
        return nil, err
    }

    return entrys.Items, nil
}

func extractName(Input string) (string) {
	r, _ := regexp.Compile(`\((\w+)\)`)
	Name := r.FindStringSubmatch(Input)

	if len(Name) == 2 {
		return Name[1]
	} else {
		return ""
	}
}

func main() {
	// wget -O cve.xml https://nvd.nist.gov/download/nvd-rss.xml
	resp, err := http.Get("https://nvd.nist.gov/download/nvd-rss.xml")
	defer resp.Body.Close()
	out, err := os.Create("/tmp/cve.xml")
	if err != nil {
		fmt.Println("Can not create temporary file in /tmp/")
		os.Exit(1)
	}
	defer out.Close()
	io.Copy(out, resp.Body)

	xmlFile, err := os.Open("/tmp/cve.xml")
	if err != nil {
		fmt.Println("Error opening file:", err)
		return
	}

	defer xmlFile.Close()
	entries, err := readCVE(xmlFile)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	repos := []string{"core", "extra", "community"}
	var db []Package
	for _, r := range repos {
		db, err = getSyncDb("/var/lib/pacman", r)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			continue
		}
	}

	for _, value := range entries {
		name := extractName(value.CVEid)
		for _, pkg := range db {
			if strings.Contains(name, pkg.Name) || name == pkg.Name {
				fmt.Printf("CVE: %s - Name %s - Package Name/Version %s/%s \nDescription: %s\nLink: %s\n\n", value.CVEid, name, pkg.Name, pkg.Version, value.Description, value.Link)
			}

		}
	}
}
