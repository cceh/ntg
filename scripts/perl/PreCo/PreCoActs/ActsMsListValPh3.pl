#! /usr/bin/perl -w
# ActsMsListVal.pl -- MySQL:Textwert:ivv7srv16.uni-muenster.de
# fuellt die Tabelle ActsMsListVal
# Vorlage von Klaus Wachtel, bearbeitet von volker.krueger@uni-muenster.de

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_CBGMPh3:localhost";	# data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });


###BEI NEUEM KAPITEL NEU EINGEBEN##########
#Nummer des aktuell bearbeiteten Kapitels 
my $chn = $ARGV[0];
### INTERAKTIVER AUFRUF DES SKRIPTS ###
if(0) # Interaktiven Aufruf ein- bzw. ausschalten
{
    print "Bitte Kapitel eingeben: ";
    chomp($chn = <STDIN>);
}
### INTERAKTIV ENDE ###
#Fuer die Summierung
my $maxchn = 28;
###########################################

my $chnstr;
if ($chn < 10)
{
	$chnstr = '0'.$chn;
} else {
	$chnstr = $chn;
}

my $target = '`ECM_Acts_Mss`.`ActsMsListValPh3`'; # ggf. Phase 2
my $source1 = '`ECM_Acts_CBGMPh3`.`Acts'.$chnstr.'att_3`';
my $source2 = '`ECM_Acts_BasePh3`.`05'.$chnstr.'Rdg`';
my $source3 = '`ECM_Acts_Mss`.`ActsMsList_2`';

my $f1 = 'SUMTXT'.$chn;
my $f2 = 'SUMMT'.$chn;
my $f3 = 'UEMT'.$chn;
my $f4 = 'QMT'.$chn;

#Fuer eine Abfrage in ActsMsList brauche ich die Nummer als String
my $chnstr2 = 'Apg'.$chnstr;

my ($ary, @ary, $sth, @msl, $ms, $byz, $byzzahl, $sumtxt, $summt, $uemt);

#Liste der zu bearbeitenden Hss.
$sth = $dbh->prepare ("SELECT HSNR FROM $target" );
$sth->execute();

while (@ary = $sth->fetchrow_array())
{
	@msl = (@msl, $ary[0]);
}

#Fuer jedes Element vom @msl...
foreach $ms(@msl)
{
	#...setze ich zunächst die Summierungsvariablen auf 0...
	$sumtxt = 0;
	$summt = 0;
	$uemt = 0;
	
	#...und mache einen Auszug der bezeugten Lesarten aus Acts01att
	$sth = $dbh->prepare ("SELECT ANFADR, ENDADR, LABEZ FROM $source1 WHERE HSNR = $ms" );
	$sth->execute();

	#Ich gehe den Auszug durch und überprüfe zunächst, ob die Handschrift im aktuellen Kapitel Text hat.
	my $text = $dbh->selectrow_array ("SELECT `$chnstr2` FROM $source3 WHERE MS = $ms");
	#print "text: $text und ms: $ms\n";	
	#Wenn die Handschrifte Text hat...
	if ($text > 0)
	{
	
		#...prüfe ich, ob eine Übereinstimmung mit der Mehrheitslesart vorliegt.
		while (@ary = $sth->fetchrow_array())
		{
			#Wenn die Handschrift bei zz, zv, zu oder zw steht...
			if ($ary[2] eq 'zz' or $ary[2] eq 'zv' or $ary[2] eq 'zu' or $ary[2] eq 'zw')
			{
				#...gehe ich ohne etwas zu tun zum nächsten Datensatz.
				next;
		
			#Wenn die Handschrift eine Variante bezeugt, setze ich $sumtxt, die Zahl der belegten Stellen, +1, überprüfe, ob diese Variante nach Acts<n>rdg die Mehrheitslesart ist. Wenn ja, setze ich  $summt, die Zahl der belegten Stellen mit bestimmter Mehrheitslesart, +1. Dann überprüfe ich, ob die bezeugte Variante gleich der Mehrheitslesart ist. Wenn ja: $uemt, Übereinstimmungen mit dem Mehrheitstext, +1.

			} else {
				$sumtxt = $sumtxt + 1;
			
				#Haben wir an dieser Stelle eine Mehrheitslesart bestimmen koennen?
				my $testbyz = $dbh->selectrow_array ("SELECT LABEZ FROM $source2 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND BYZ LIKE 'B'");
			
				if (defined $testbyz)
				{
					$summt = $summt + 1;
				
					if ($testbyz eq $ary[2])
					{
						$uemt = $uemt + 1;
					}
				
					undef $testbyz;								
				}
			}
		}
	}
	
	#ich trage die ermittelten Werte in ActsMsListVal ein und summiere alle bisher ermittelten Werte in den Feldern SUMTXT, SUMMT, UEMT.
	
	$dbh->do ("UPDATE $target SET `$f1` = $sumtxt, `$f2` = $summt, `$f3` = $uemt WHERE HSNR = $ms");
	
	#Prozentwert QMT (Quote Mehrheitstext) ermitteln u. eintragen
	#Wenn man dabei die Zahl der Stellen, an denen MT bestimmt wurde, zugrunde legt, führt das dazu, dass bei Byz-Hss. die Schwellenwerte für Gruppierungen so hoch gehen, dass die Übereinstimmungen an Stellen, an denen diese Hss. vom MT abweichen, nicht dazu führen können, dass die Quote der Übereinstimmungen mit MT übertroffen wird. Wenn es darum geht, auch innerbyzantinische Gruppierungen sichtbar zu machen, müssen die MT-Quoten auf der Basis sämtlicher Stellen berechnet werden, die in einer Hs. belegt sind.
	
	#$dbh->do ("UPDATE $target SET `$f4` = $uemt*100/$summt WHERE HSNR = $ms AND `$f2`>0");
	$dbh->do ("UPDATE $target SET `$f4` = $uemt*100/$sumtxt WHERE HSNR = $ms AND `$f1`>0");
	
}

#Summierung
#Bereits eingegebene Werte löschen
$dbh->do ("UPDATE $target SET `SUMTXT` = 0");
$dbh->do ("UPDATE $target SET `SUMMT` = 0");
$dbh->do ("UPDATE $target SET `UEMT` = 0");
$dbh->do ("UPDATE $target SET `QMT` = 0");

my $n = 0;
while ($n < $maxchn)
{
	$n++;
	my $fz1 = '`SUMTXT'.$n.'`';
	my $fz2 = '`SUMMT'.$n.'`';
	my $fz3 = '`UEMT'.$n.'`';
	
	$dbh->do ("UPDATE $target SET `SUMTXT` = `SUMTXT`+$fz1, `SUMMT` = `SUMMT`+$fz2, `UEMT` = `UEMT`+$fz3");
}
		
#Prozentwert QMT nach Summierung
#$dbh->do ("UPDATE $target SET `QMT` = `UEMT`*100/`SUMMT` WHERE HSNR = $ms AND `SUMMT`>0");
$dbh->do ("UPDATE $target SET `QMT` = `UEMT`*100/`SUMTXT` WHERE `SUMTXT`>0");
	
$sth->finish ();

$dbh->disconnect ();

exit (0);
