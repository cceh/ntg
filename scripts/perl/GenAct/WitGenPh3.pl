#! /usr/bin/perl -w
# WitGen.pl -- MySQL:CBGM_CL2_Base:ivv7srv16.uni-muenster.de
# WitGen-Tabellen aus <n>Witn-Tabellen erzeugen u. entspr. zu LocStemEd erweitern
# Vorlage von Klaus Wachtel, weiter bearbeitet von Volker Krüger

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_BasePh3:localhost";   # data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

my $debug = 0;

### AKTUELL ZU BEARBEITENDES BUCH UND KAPITEL ###
my $book = '05';
my $chap = $ARGV[0];
my $chapstr = '';
if ($chap < 10)
{
    $chapstr = '0' . $chap;
}
else
{
    $chapstr = $chap;
}

### INTERAKTIVER AUFRUF DES SKRIPTS ###
#if(0) # Interaktiven Aufruf ein- bzw. ausschalten
#{
#    print "Bitte Nummer des neutestamentlichen Buches eingeben (zweistellig): ";
#    chomp($book = <STDIN>); # Zeilenumbruch entfernen mit chomp()
#    print "Bitte Kapitel eingeben (zweistellig): ";
#    chomp($chap = <STDIN>);
#}
### INTERAKTIV ENDE ###

my $source11 = '`VarGenAtt_ActPh3`.`LocStemEdAct'.$chapstr.'`';
my $source12 = '`VarGenAtt_ActPh3`.`VarGenAttAct'.$chapstr.'`';
#my $source2 = '`ECM_Acts_BasePh3`.`'.$book.$chapstr.'Witn`';
# do not copy data from ECM_Acts_Base.0501Witn anymore
# but from VarGenAtt_Act.VarGenAttAct01 instead.
# doing this way one gets all the splitted variants.
my $target = '`ECM_Acts_BasePh3`.`'.$book.$chapstr.'WitGen`';

my ($sth, @ary, $ary, $q1);

### NEUE ERGEBNISTABELLE ANLEGEN ###
$dbh->do ("DROP TABLE IF EXISTS $target;");
	$dbh->do ("CREATE  TABLE  $target (  
	 `ANFADR` int( 11  )  default NULL ,
	 `ENDADR` int( 11  )  default NULL ,
	 `LABEZ` varchar( 2  )  collate utf8_unicode_ci  default NULL ,
	 `HSNR` int( 6  )  default NULL
	  ) ENGINE  = InnoDB  DEFAULT CHARSET  = utf8 COLLATE  = utf8_unicode_ci;");
#$dbh->do ("INSERT INTO $target SELECT ANFADR, ENDADR, LABEZ, HSNR FROM $source2 WHERE 1");
$dbh->do ("INSERT INTO $target SELECT BEGADR, ENDADR, VARID, MS FROM $source12 WHERE 1");
$dbh->do ("ALTER TABLE $target ADD `LABNEU` varchar( 2  ), ADD `Q1` varchar( 2  ), ADD `Q2` varchar( 2  ), ADD `CHECK` varchar( 1  ) ;");
$dbh->do ("ALTER TABLE $target ADD INDEX  (`ANFADR`,`ENDADR`)");

#### LocStemEd-Tabelle + VarGenAtt abfragen ####
$sth = $dbh->prepare ("SELECT a.`BEGADR`, a.`ENDADR`, a.`VARID`, a.`VARNEW`, a.`S1`, a.`S2`, b.`MS` FROM $source11 a, $source12 b 
        WHERE a.`BEGADR` = b.`BEGADR` AND a.`ENDADR` = b.`ENDADR` AND a.`VARID` = b.`VARID` AND a.`VARNEW` = b.`VARNEW`; "); 
$sth->execute();

#0 BEGADR, 1 ENDADR, 2 VARID, 3 VARNEW, 4 S1, 5 S2, 6 MS(=HSNR)
	
while (@ary = $sth->fetchrow_array())
{
	my $cmd = "UPDATE $target SET `LABNEU` = '$ary[3]', `Q1` = '$ary[4]', `Q2` = '$ary[5]' WHERE `ANFADR` = $ary[0] AND `ENDADR` = $ary[1] AND `LABEZ` LIKE '$ary[2]' AND `HSNR` = '$ary[6]'; ";
	if ($debug) { print "$cmd\n"; }
	$dbh->do ($cmd);
}

$dbh->do ("UPDATE $target SET `LABNEU` = `LABEZ` WHERE `LABEZ` LIKE 'zz' OR `LABEZ` LIKE 'zx' OR 
			`LABEZ` LIKE 'zw' OR `LABEZ` LIKE 'zv' OR `LABEZ` LIKE 'zu' ; ");

## We do not want to count A if the source is unknown.
$dbh->do("UPDATE $target SET LABEZ = 'zz', LABNEU = 'zz' WHERE Q1 = '?' AND HSNR = 0; ");
##

$sth->finish ();

$dbh->disconnect ();

exit (0);
