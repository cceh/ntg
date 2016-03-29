#! /usr/bin/perl -w
# Acts_Base.pl -- MySQL:ECM_Acts_Base:ivv7srv16.uni-muenster.de
# Variantenspektren in ECM_Acts_Sp fŸr Hss. einzelner Kapitel auf der Basis von ECM_Acts_Base anlegen
# Klaus Wachtel

use strict;
use DBI;
use access;

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_Base:localhost";	# data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password


my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

###AKTUELL ZU BEARBEITENDES KAPITEL###
my $chn = $ARGV[0];
### INTERAKTIVER AUFRUF DES SKRIPTS ###
if(0) # Interaktiven Aufruf ein- bzw. ausschalten
{
    print "Bitte Kapitel eingeben: ";
    chomp($chn = <STDIN>);
}
### INTERAKTIV ENDE ###
my $chnstr;
if ($chn < 10)
{
	$chnstr = '0'.$chn;
} else {
	$chnstr = $chn;
}

my $source = '`ECM_Acts_CBGMPh3`.`Acts'.$chnstr.'att_3`';    # z.B. ECM_Acts_CBGMPh2.Acts01att_2

my $target1 = '`ECM_Acts_BasePh3`.`05'.$chnstr.'VP`';      # z.B. ECM_Acts_Base.0501VP
my $target2 = '`ECM_Acts_BasePh3`.`05'.$chnstr.'Rdg`';     # z.B. ECM_Acts_Base.0501Rdg
my $target3 = '`ECM_Acts_BasePh3`.`05'.$chnstr.'Witn`';    # z.B. ECM_Acts_Base.0501Witn

my ($sth, @ary, $ary, $gtxt, $ueges, $lac, $hsnr, @msl, $ms, @cpmsl, $cpms);

#(1) VP - variant passages
$dbh->do ("DROP TABLE IF EXISTS $target1;");

$dbh->do (" CREATE  TABLE  $target1 (  
 `ANFADR` int( 11  )  default NULL ,
 `ENDADR` int( 11  )  default NULL 
 ) ENGINE  = InnoDB  DEFAULT CHARSET  = utf8 COLLATE  = utf8_unicode_ci;");

$dbh->do ("INSERT INTO $target1 SELECT DISTINCT ANFADR, ENDADR FROM $source ORDER BY ANFADR, ENDADR DESC;");

$dbh->do ("ALTER TABLE $target1 ADD `BZdef` INT(1) NOT NULL, ADD `CHECK` VARCHAR(1) NOT NULL;");


#(2) rdg - Auslistung der Lesarten
$dbh->do ("DROP TABLE IF EXISTS $target2;");

$dbh->do ("CREATE  TABLE  $target2 (  
 `ANFADR` int( 11  )  default NULL ,
 `ENDADR` int( 11  )  default NULL ,
 `LABEZ` varchar( 32  )  collate utf8_unicode_ci  default NULL ,
 `LABEZSUF` varchar( 32  )  collate utf8_unicode_ci  default NULL ,
 `LESART` varchar( 1024  )  character  set utf8 collate utf8_bin  default NULL 
  ) ENGINE  = InnoDB  DEFAULT CHARSET  = utf8 COLLATE  = utf8_unicode_ci;");

$dbh->do ("INSERT INTO $target2 SELECT DISTINCT ANFADR, ENDADR, LABEZ, LABEZSUF, LESART FROM $source ORDER BY ANFADR, ENDADR DESC, LABEZ;");

$dbh->do ("DELETE FROM $target2 WHERE LABEZ LIKE 'zu' OR LABEZ LIKE 'zv' OR LABEZ LIKE 'zw' OR LABEZ LIKE 'zy' OR LABEZ LIKE 'zz'");

$sth = $dbh->prepare ("SELECT ANFADR, ENDADR, LABEZ, LABEZSUF FROM $target2 WHERE LABEZSUF NOT LIKE ''" );
$sth->execute();

while (@ary = $sth->fetchrow_array())
{
	my $testlab = $dbh->selectrow_array ("SELECT LABEZ FROM $target2 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND LABEZ LIKE '$ary[2]' AND LABEZSUF LIKE ''");
	
	if (defined $testlab)
	{
		$dbh->do ("DELETE FROM $target2 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1] AND LABEZ LIKE '$ary[2]' AND LABEZSUF LIKE '$ary[3]'");
	}
}

$dbh->do ("ALTER TABLE $target2 ADD `CHECK` VARCHAR(1) NOT NULL, ADD `BZ` INT(1) NOT NULL, ADD `BZdef` INT(1) NOT NULL, ADD `BYZ` VARCHAR(1) NOT NULL;");

#(3)Witn - Bezeugungstabelle
$dbh->do ("DROP TABLE IF EXISTS $target3;");

$dbh->do ("CREATE  TABLE  $target3 (  
`ANFADR` int( 11  )  default NULL ,
`ENDADR` int( 11  )  default NULL ,
`LABEZ` varchar( 32  )  collate utf8_unicode_ci  default NULL ,
`LABEZSUF` varchar( 32  )  collate utf8_unicode_ci  default NULL ,
`HSNR` int( 11  )  default NULL ,
`HS` varchar( 32  )  collate utf8_unicode_ci  default NULL 
) ENGINE  = InnoDB  DEFAULT CHARSET  = utf8 COLLATE  = utf8_unicode_ci;");

$dbh->do ("INSERT INTO $target3 SELECT DISTINCT ANFADR, ENDADR, LABEZ, LABEZSUF, HSNR, HS FROM $source ORDER BY ANFADR, ENDADR, LABEZ, HSNR;");

$sth->finish ();

$dbh->disconnect ();

exit (0);
