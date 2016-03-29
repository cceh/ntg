#! /usr/bin/perl -w
# VGCL_all.pl -- MySQL:Textwert:ivv7srv16.uni-muenster.de
# <$book><$chap>GenTab_2 schriftweise füllen auf der Basis von 
# Vergleichen einzelner Variantenspektren in `ECM_Acts_Sp_NN`
# Vorlage von Klaus Wachtel, weiter bearbeitet von Volker Krüger
# Das Einfügen der Vergleichshandschriften wurde aus VG05_all.pl importiert.
# VG05_all.pl muss nicht mehr ausgeführt werden. 

use strict;
use DBI;
use access;
#use Fehlvers;

sub isFehlvers;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_Sp_01Ph3:localhost"; 	# data source name
my $user_name = getUsername();							# user name
my $password = getPassword();							# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

my $DEBUG = 0;
my $sql;
my $DB_VG = 'ECM_Acts_VGPh3';

###AKTUELL ZU BEARBEITENDE SCHRIFT###
my $book = '05';
my $chap = $ARGV[0];
my $chnstr = '';

if ($chap < 10)
{
	if ($chap == 0)
	{
		$chnstr = '0';
	}
	else
	{
		$chnstr = '0'.$chap;
	}
} else {
	$chnstr = $chap;
}

my $source1 = '`ECM_Acts_Mss`.`ActsMsList_2`'; # unverändert immer ECM_Acts_Mss.ActsMsList - wer hat wo Text?
#  $source2 z.B. ECM_Acts_Sp_01.Acts01_100740 Vergleichspartner 1
#  $source3 z.B. ECM_Acts_Sp_01.Acts01_317040 Vergleichspartner 2

######################################################
$dbh->do ("UPDATE $source1 SET `CHECK` = '' WHERE 1");
######################################################

my $target = '`'.$DB_VG.'`.`'.$book.$chnstr.'GenTab_2`'; # z.B. ECM_Acts_VG.0502GenTab_2
#print $target;
#exit(0);

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
# Suche alle Papyri, Majuskeln und Minuskeln, die im ausgewählten Kapitel (mindestens teilweise) Text haben
$sth = $dbh->prepare ("SELECT MS FROM $source1 WHERE `Apg$chnstr` = 1 AND `CHECK` NOT LIKE '.' "); #AND MS < 400000");
$sth->execute();

while (@ary = $sth->fetchrow_array())
{
    @msl = (@msl, @ary);
}

# Daten per insert einlesen
foreach $ms(@msl)
{
    $dbh->do ("UPDATE $source1 SET `CHECK` = '.' WHERE MS = $ms"); # $source1 = '`ECM_Acts_Mss`.`ActsMsList`';
    $sql = "SELECT MS FROM $source1 WHERE `Apg$chnstr` = 1 AND `CHECK` NOT LIKE '.' "; # AND MS < 400000";
    if ($DEBUG) { print __LINE__." $sql\n"; }
    $sth = $dbh->prepare ($sql);
    $sth->execute();
    while (@ary = $sth->fetchrow_array())
    {
        @cpmsl = (@cpmsl, @ary);
    }
    foreach $cpms(@cpmsl)
    {
        $dbh->do ("INSERT INTO $target (MS1, MS2) VALUES ($ms, $cpms)"); # $target z.B. ECM_Acts_VG.0501GenTab_2
    }
    undef @cpmsl;
}

# Damit Supplemente derselben Handschrift nicht mit einander oder mit supplementierten Handschriften
# verglichen werden
$dbh->do("DELETE FROM $target WHERE `MS2` = `MS1`+1 OR `MS2` = `MS1`+2; ");

# Vergleichen der Tabellen und Zählen der Übereinstimmungen
foreach $ms(@msl)
{
	my $source2 = '`ECM_Acts_Sp_'.$chnstr.'Ph3`.`Acts'.$chnstr.'_'.$ms.'`'; # z.B. ECM_Acts_Sp_01.Acts01_100740
	$sql = "SELECT `MS2` FROM $target WHERE `MS1` = $ms";
	if ($DEBUG) { print __LINE__." $sql\n"; }
	$sth = $dbh->prepare ($sql);
	$sth->execute();

	while (@ary = $sth->fetchrow_array())
	{
		@cpmsl = (@cpmsl, @ary);
	}
	
	foreach $cpms(@cpmsl)
	{
		my $source3 = '`ECM_Acts_Sp_'.$chnstr.'Ph3`.`Acts'.$chnstr.'_'.$cpms.'`'; # z.B. ECM_Acts_Sp_01.Acts01_317040
		$sql = "SELECT `ANFADR`, `ENDADR`, `LABEZ`, `LABNEU`, `Q1`, `Q2` FROM $source2";
		if ($DEBUG) { print __LINE__." $sql\n"; }
		$sth = $dbh->prepare ($sql); # z.B. ECM_Acts_Sp_01.Acts01_100740
		$sth->execute();
### 0 ANFADR, 1 ENDADR, 2 LABEZ, 3 LABNEU, 4 Q1, 5 Q2
		
		$gtxt  = 0;
		$ueges = 0;
		$w1fw2 = 0;
		$w1tw2 = 0;
		$uncl  = 0;
		$norel = 0;
		
		while (@ary = $sth->fetchrow_array())
		{
			my $anfadr = $ary[0];
			my $endadr = $ary[1];
			#my $b_fehlvers = isFehlvers($anfadr, $endadr);
			## 0 = Fehlvers
			## 1 = kein Fehlvers
			#if (!$b_fehlvers)
			#{
			#	next;
			#}
			
			if ($ary[3] eq 'zz' or $ary[3] eq 'zv' or $ary[3] eq 'zu' or $ary[3] eq 'zw' or $ary[3] eq 'zx')
			{
				next;
			} else {
				$sql = "SELECT `LABEZ`, `LABNEU`, `Q1`, `Q2` FROM $source3 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1]";
				if ($DEBUG) { print __LINE__." $sql\n"; }
				my ($cplabez, $cplabneu, $cpq1, $cpq2) = $dbh->selectrow_array ($sql);
						
				if (not defined $cplabez)	
				{
					print "cplabez nicht definiert bei $source3\n$ary[0] $ary[1] $cplabez\n";
					print "source2 ist $source2\n";
					exit (1);
				}	

				if ($cplabneu eq 'zz' or $cplabneu eq 'zv' or $cplabneu eq 'zu' or $cplabneu eq 'zw' or $cplabneu eq 'zx')
				{
					next;
				} else {
			
					if (not defined $cpq1)	
					{
						print "\ncpq1 nicht definiert bei $source3\n$ary[0] $ary[1] $cplabez\n";
						exit (2);
					}	
					
					$gtxt = $gtxt+1;
					
					if ($ary[3] =~ /\d/ or $cplabneu =~ /\d/) 
					##bei Splits wird labez ausgewertet
					{
						if ($ary[2] eq $cplabez)
						{
							$ueges = $ueges+1;
						}
						
						if (($cpq1 eq '?' or $ary[4] eq '?' or $ary[5] eq '?') and $ary[2] ne $cplabez and $cpq1 ne $ary[3] and $cplabneu ne $ary[4] and $cplabneu ne $ary[5])
						##wenn die vergl. Hss. von einander abweichen u. eine von ihnen Q1 = '?' hat, UND KEINE VON IHNEN QUELLE DER ANDEREN IST, ist die Beziehung 'UNCLEAR'
						{
							$uncl++;
						}
					
						if ($ary[2] ne $cplabez and $cpq1 ne '?' and $ary[4] ne '?' and $ary[5] ne '?' and $ary[4] ne $cplabneu and $cpq1 ne $ary[3] and $ary[5] ne $cplabneu)
						##wenn die vergl. Hss. von einander abweichen u. die eine nicht die Quellvariante der Variante der anderen, aber auch nicht Q1 = '?' hat, stehen sie nicht in direkter Beziehung zu einander. 
						{
							$norel++;
						}

					} else {
					##in allen anderen Fällen wird labneu ausgewertet
						if ($ary[3] eq $cplabneu)
						{
							$ueges = $ueges+1;
						}						
					
					
						if (($cpq1 eq '?' or $ary[4] eq '?' or $ary[5] eq '?') and $ary[3] ne $cplabneu and $cpq1 ne $ary[3] and $cplabneu ne $ary[4] and $cplabneu ne $ary[5])
						##wenn die vergl. Hss. von einander abweichen u. eine von ihnen Q1 = '?' hat, ist die Beziehung 'UNCLEAR'
						{
							$uncl++;
						}
					
						if ($ary[3] ne $cplabneu and $cpq1 ne '?' and $ary[4] ne '?' and $ary[5] ne '?' and $ary[4] ne $cplabneu and $cpq1 ne $ary[3] and $ary[5] ne $cplabneu)
						##wenn die vergl. Hss. von einander abweichen u. die eine nicht die Quellvariante der Variante der anderen, aber auch nicht Q1 = '?' hat, 
						##stehen sie nicht in direkter Beziehung zu einander. 
						{
							$norel++;
						}
					}

					if  ($cpq1 eq $ary[3])
					##wenn die Ausgangsshs. die prioritäre Variante enthält
					{
						$w1tw2++;
					}
					if  ($cplabneu eq $ary[4])
					##wenn die Vergleichshs. die prioritäre Variante enthält
					{
						$w1fw2++;
						if ($DEBUG)
						{
							print "\$cplabneu ist $cplabneu\n";
							print "\$ary[4] ist $ary[4]\n";
						}
					}
					if ($cplabneu eq $ary[5])
					##wenn die andere Vergleichshs. die prioritäre Variante enthält
					{
						$w1fw2++;
						# DEBUG-Ausgabe
						if ($DEBUG)
						{
							print "\$cplabneu ist $cplabneu\n";
							print "\$ary[5] ist $ary[5]\n";
						}
						
					}
					
				}
			}	
		}
		
		if ($w1fw2 > $w1tw2)
		##wenn die Anzahl der prioritären Varianten in W2 größer ist
		{
			$dbh->do ("UPDATE $target SET `PASSAGES` = $gtxt, `EQ` = $ueges, `PERC1` = $ueges*100/$gtxt, `W1FW2` = $w1fw2, `W1TW2` = $w1tw2, `UNCLEAR` = $uncl, `NOREL` = $norel, `DIFF` = $gtxt-$ueges, `DIR` = '<--' WHERE `MS1`=$ms AND `MS2`=$cpms");
		} else {
		
			##wenn die Anzahl der prioritären Varianten in W1 größer ist
			if ($w1fw2 < $w1tw2)
			{
				$sql = "UPDATE $target SET `PASSAGES` = $gtxt, `EQ` = $ueges, `PERC1` = $ueges*100/$gtxt, `W1FW2` = $w1fw2, `W1TW2` = $w1tw2, `UNCLEAR` = $uncl, `NOREL` = $norel, `DIFF` = $gtxt-$ueges, `DIR` = '-->' WHERE `MS1`=$ms AND `MS2`=$cpms";
				$dbh->do ($sql);
			} else {
				$sql = "UPDATE $target SET `PASSAGES` = $gtxt, `EQ` = $ueges, `PERC1` = $ueges*100/$gtxt, `W1FW2` = $w1fw2, `W1TW2` = $w1tw2, `UNCLEAR` = $uncl, `NOREL` = $norel, `DIFF` = $gtxt-$ueges WHERE `MS1`=$ms AND `MS2`=$cpms";
				$dbh->do ($sql);
			}
			if ($DEBUG) { print __LINE__." $sql\n"; }
		}
        # Update des Feldes Witn2
        # FIXME: Eigentlich kann man diesen Schritt bereits beim ersten Insert erledigen!
        my @res;
        $sth = $dbh->prepare("SELECT `WITN` FROM $source1 WHERE `MS` = $cpms; ");
        $sth->execute();
        @res = $sth->fetchrow_array();
        $dbh->do("UPDATE $target SET `WITN2` = '$res[0]' WHERE `MS2` = $cpms; ");
	}
    
    # Update des Feldes Witn1
    my @res;
    $sth = $dbh->prepare("SELECT `WITN` FROM $source1 WHERE `MS` = $ms; ");
    $sth->execute();
    @res = $sth->fetchrow_array();
    $dbh->do("UPDATE $target SET `WITN1` = '$res[0]' WHERE `MS1` = $ms; ");
	
	undef @cpmsl;
	$dbh->do ("UPDATE $source1 SET `CHECK` = '.' WHERE `MS` = $ms");
}

$dbh->do ("DELETE FROM $target WHERE `PASSAGES` = 0");

$sth->finish ();

$dbh->disconnect ();

exit (0);
