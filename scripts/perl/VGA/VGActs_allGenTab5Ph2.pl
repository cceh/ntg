#! /usr/bin/perl -w
# VGCL_all.pl -- MySQL:Textwert:ivv7srv16.uni-muenster.de
# CLGenTab2_2 füllen auf der Basis von <$writ>GenTab_2
# Vorlage von Klaus Wachtel, Anpassung Apostelgeschichte von Volker Krüger

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_VG:localhost";	# data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password
my $DEBUG = 0;

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

my $source1 = '`ECM_Acts_Mss`.`ActsMsList_2`';

######################################################
$dbh->do ("UPDATE $source1 SET `CHECK` = '' WHERE 1");
######################################################

my $target = '`ECM_Acts_VGPh2`.`0530GenTab_2`';

# Tabelle löschen, falls schon vorhanden
$dbh->do ("DROP TABLE IF EXISTS $target;");

# Tabelle neu anlegen
$dbh->do("CREATE TABLE $target (
  `WITN1` varchar(10) NOT NULL default '',
  `WITN2` varchar(10) NOT NULL default '',
  `DIR` varchar(4) NOT NULL default '',
  `NR` int(3) NOT NULL default '0',
  `MS1` int(6) NOT NULL default '0',
  `MS2` int(6) NOT NULL default '0',
  `EQ` int(4) NOT NULL default '0',
  `W1FW2` int(4) NOT NULL default '0',
  `W1TW2` int(4) NOT NULL default '0',
  `UNCLEAR` int(4) NOT NULL default '0',
  `NOREL` int(4) NOT NULL default '0',
  `PASSAGES` int(4) NOT NULL default '0',
  `DIFF` int(4) NOT NULL default '0',
  `PERC1` decimal(6,3) NOT NULL default '0.000',
  `PERC2` decimal(6,3) NOT NULL default '0.000',
  `PERC3` decimal(6,3) NOT NULL default '0.000',
  `PERC4` decimal(6,3) NOT NULL default '0.000',
  `CHECK` char(1) NOT NULL default '',
  KEY `hsnr` (`MS1`,`MS2`),
  KEY `MS1` (`MS1`,`MS2`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE  = utf8_unicode_ci; ");

my ($sth, @ary, $ary, $gtxt, $ueges, $w1fw2, $w1tw2, $uncl, $norel, $lac, $hsnr, @msl, $ms, @cpmsl, $cpms);

# Vergleichspaare einfügen, d.h. jede Ms soll mit jeder anderen verglichen werden:
# Suche alle Papyri, Majuskeln und Minuskeln, die in Acta (mindestens teilweise) Text haben,
# d.h. hier sind auch die Fragmente eingeschlossen.
$sth = $dbh->prepare ("SELECT MS FROM $source1 WHERE  `CHECK` NOT LIKE '.' AND MS < 400000"); # without: `Apg` = 1 AND
$sth->execute();

while (@ary = $sth->fetchrow_array())
{
    if ($DEBUG) {
	print "@ary\n";
    }
    @msl = (@msl, @ary);
}

# Daten per insert einlesen
foreach $ms(@msl)
{
	# Aktuell in Arbeit befindlicher Datensatz mit check = '.' markiert
    $dbh->do ("UPDATE $source1 SET `CHECK` = '.' WHERE MS = $ms");
    
    $sth = $dbh->prepare ("SELECT MS FROM $source1 WHERE `CHECK` NOT LIKE '.' AND MS < 400000"); 
    $sth->execute();
    
    while (@ary = $sth->fetchrow_array())
    {
        @cpmsl = (@cpmsl, @ary);
    }
    
    foreach $cpms(@cpmsl)
    {
    	my ($witn1, $witn2);
    	$witn1 = $dbh->selectrow_array("SELECT `WITN` FROM $source1 WHERE `MS` = $ms;");
    	$witn2 = $dbh->selectrow_array("SELECT `WITN` FROM $source1 WHERE `MS` = $cpms;");
    	my $s = "INSERT INTO $target (MS1, MS2, WITN1, WITN2) VALUES ($ms, $cpms, '$witn1', '$witn2')";
        $dbh->do ($s);
    	if ($DEBUG)
    	{
    		print "$s\n";
    	}
    }
    
    undef @cpmsl;
}

# Damit Supplemente derselben Handschrift nicht mit einander oder mit supplementierten Handschriften
# verglichen werden
$dbh->do("DELETE FROM $target WHERE `MS2` = `MS1`+1 OR `MS2` = `MS1`+2; ");

my @wlist = ('`ECM_Acts_VGPh2`.`0501GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0502GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0503GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0504GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0505GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0506GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0507GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0508GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0509GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0510GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0511GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0512GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0513GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0514GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0515GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0516GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0517GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0518GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0519GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0520GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0521GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0522GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0523GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0524GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0525GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0526GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0527GenTab_2`'
			, '`ECM_Acts_VGPh2`.`0528GenTab_2`'
			);

$sth = $dbh->prepare ("SELECT MS FROM $source1 WHERE `CHECK` NOT LIKE '.' AND MS < 400000");
$sth->execute();
	
while (@ary = $sth->fetchrow_array())
{
	@msl = (@msl, @ary);
}

foreach $ms(@msl)
{
	$sth = $dbh->prepare ("SELECT `MS2` FROM $target WHERE `MS1` = $ms");
	$sth->execute();
	
	while (@ary = $sth->fetchrow_array())
	{
		@cpmsl = (@cpmsl, @ary);
	}
	
	foreach $cpms(@cpmsl)
	{
		
		$gtxt  = 0;
		$ueges = 0;
		$w1fw2 = 0;
		$w1tw2 = 0;
		$uncl  = 0;
		$norel = 0;
		
		my ($g, $ue, $wf, $wt, $uc, $nr, $w);
		
		foreach $w(@wlist)
		{
			($g, $ue, $wf, $wt, $uc, $nr) = $dbh->selectrow_array ("SELECT `PASSAGES`, `EQ`, `W1FW2`, `W1TW2`, `UNCLEAR`, `NOREL` FROM $w WHERE `MS1` = $ms AND `MS2` = $cpms");
			
			if (not defined $g)
			{
				next;
			}
		
			$gtxt  = $gtxt  + $g;
			$ueges = $ueges + $ue;
			$w1fw2 = $w1fw2 + $wf;
			$w1tw2 = $w1tw2 + $wt;
			$uncl  = $uncl  + $uc;
			$norel = $norel + $nr;
		}
		
		if ($w1fw2 > $w1tw2)
		##wenn die Anzahl der prioritären Varianten in W2 größer ist
		{
			$dbh->do ("UPDATE $target SET `PASSAGES` = $gtxt, `EQ` = $ueges, `PERC1` = $ueges*100/$gtxt, `W1FW2` = $w1fw2, `W1TW2` = $w1tw2, `UNCLEAR` = $uncl, `NOREL` = $norel, `DIFF` = $gtxt-$ueges, `DIR` = '<--' WHERE `MS1`=$ms AND `MS2`=$cpms");
		} 
		##wenn die Anzahl der prioritären Varianten in W1 größer ist
		elsif ($w1fw2 < $w1tw2)
		{
			$dbh->do ("UPDATE $target SET `PASSAGES` = $gtxt, `EQ` = $ueges, `PERC1` = $ueges*100/$gtxt, `W1FW2` = $w1fw2, `W1TW2` = $w1tw2, `UNCLEAR` = $uncl, `NOREL` = $norel, `DIFF` = $gtxt-$ueges, `DIR` = '-->' WHERE `MS1`=$ms AND `MS2`=$cpms");
		}
		##wenn die Anzahl jeweils gleich ist
		else 
		{
			$dbh->do ("UPDATE $target SET `PASSAGES` = $gtxt, `EQ` = $ueges, `PERC1` = $ueges*100/$gtxt, `W1FW2` = $w1fw2, `W1TW2` = $w1tw2, `UNCLEAR` = $uncl, `NOREL` = $norel, `DIFF` = $gtxt-$ueges WHERE `MS1`=$ms AND `MS2`=$cpms");
		}
	}
	
	undef @cpmsl;
	$dbh->do ("UPDATE $source1 SET `CHECK` = '.' WHERE MS = $ms");
}

$dbh->do ("DELETE FROM $target WHERE `PASSAGES` = 0");

$sth->finish ();

$dbh->disconnect ();

exit (0);
