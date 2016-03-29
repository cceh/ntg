#! /usr/bin/perl -w
# Att2CBGM.pl 
# kopiert die Daten aus ECM_Acts_CBGM nach VarGenAtt_Act, 
# zur weiteren Bearbeitung im Stemma-Editor
# volker.krueger@uni-muenster.de

use strict;
use DBI;
use access;

# Kommandozeilenparameter checken
if (not defined $ARGV[0]) {
	print "Please enter the number of the chapter\n.";
	exit (1); 
}

#@ _VARDECL_
my $dsn = "DBI:mysql:ECM_Acts_CBGM:localhost";	# data source name
my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

###Chapter Number eintragen bzw. aus Kommandozeilenparameter übernehmen###
my $chn = $ARGV[0];
my $chnstr = '';
if ($chn < 10)
{
	$chnstr = '0'.$chn;#HERE
} else {
	$chnstr = $chn;
}
my $cmd = ''; # SQL commands
my ($sth, $sth2); # Statement handle
my (@res, @res2); # Result sets
my ($anfadr, $endadr, $labez, $res, $r2, $len);

my $source  = '`ECM_Acts_CBGMPh2`.`Acts'.$chnstr.'att_2`'; #'`ECM_Acts_CBGMPh2`.`Acts'.$chnstr.'att_2`';
my $target1 = '`VarGenAtt_ActPh2`.`LocStemEdAct'.$chnstr.'`'; #'`VarGenAtt_ActPh2`.`LocStemEdAct'.$chnstr.'`';
my $target2 = '`VarGenAtt_ActPh2`.`RdgAct'.$chnstr.'`'; #'`VarGenAtt_ActPh2`.`RdgAct'.$chnstr.'`';
my $target3 = '`VarGenAtt_ActPh2`.`VarGenAttAct'.$chnstr.'`'; #'`VarGenAtt_ActPh2`.`VarGenAttAct'.$chnstr.'`';

# Ausgangslage: alle Tabellen sind leer
$cmd = "TRUNCATE $target1;";
#print $cmd."\n";
$dbh->do ($cmd);
$cmd = "TRUNCATE $target2;";
#print $cmd."\n";
$dbh->do ($cmd);
$cmd = "TRUNCATE $target3;";
#print $cmd."\n";
$dbh->do ($cmd);

# Get all readings
$cmd  = "SELECT DISTINCT anfadr, endadr, labez ";
$cmd .= "FROM $source; ";
$sth  = $dbh->prepare($cmd);
$sth->execute();
while(@res = $sth->fetchrow_array())
{
    $anfadr = $res[0];
    $endadr = $res[1];
    $labez  = $res[2];
    #print "Checking:\n";
    #print "$anfadr/$endadr: $labez\n";
    # Insert data into witness table 
    # Take care! There is no restriction! 
    # The filter "where labezsuf is null or labezsuf = ''" 
    # is not possible here! All witnesses have to be copied
    # from ECM_Acts_CBGM to VarGenAtt_Act.
    $cmd  = "select buch, kapanf, versanf, wortanf, wortend, versend, kapend, ";
    $cmd .= "labez, labez, hs, hsnr, anfadr, endadr ";
    $cmd .= "from $source ";
    $cmd .= "where anfadr = $anfadr and endadr = $endadr ";
    $cmd .= "and labez = '$labez' "; 
	$sth2 = $dbh->prepare($cmd);
    $sth2->execute();
    while(@res2 = $sth2->fetchrow_array())
    {
        $cmd  = "insert into $target3 ";
        $cmd .= "(book, chbeg, vbeg, wbeg, wend, vend, chend, ";
        $cmd .= "varid, varnew, witn, ms, begadr, endadr) ";
        $cmd .= "values ($res2[0], $res2[1], $res2[2], $res2[3], $res2[4], $res2[5], $res2[6], ";
        $cmd .= "'$res2[7]', '$res2[8]', '$res2[9]', $res2[10], $res2[11], $res2[12])";
    	$dbh->do($cmd);
	}
    # Insert data into reading table
    $cmd  = "select distinct buch, kapanf, versanf, wortanf, kapend, versend, wortend, ";
    $cmd .= "labez, lesart, anfadr, endadr, labezsuf ";
    $cmd .= "from  $source ";
    $cmd .= "where anfadr = $anfadr and endadr = $endadr ";
    $cmd .= "and labez = '$labez' ";
    $cmd .= "and (labezsuf is null or labezsuf = ''); ";
    #print $cmd . "\n";
    $sth2 = $dbh->prepare($cmd);
    $sth2->execute();
    @res2 = $sth2->fetchrow_array();
    $len = @res2;
    if($len == 0)
    {
        $cmd  = "select distinct buch, kapanf, versanf, wortanf, kapend, versend, wortend, ";
        $cmd .= "labez, lesart, anfadr, endadr, labezsuf ";
        $cmd .= "from $source ";
        $cmd .= "where anfadr = $anfadr and endadr = $endadr ";
        $cmd .= "and labez = '$labez' ";
    }
    #print "Statement: \n";
    #print "$cmd\n";
    $sth2 = $dbh->prepare($cmd); 
    $sth2->execute();
    while(@res2 = $sth2->fetchrow_array())
    {
        my $lesart = $res2[8];
        if (!defined $lesart)
        {
            $lesart = "";
        }
        $cmd  = "insert into $target2";
        $cmd .= "(buch, kapanf, versanf, wortanf, kapend, versend, wortend, ";
        $cmd .= "labez, lesart, anfadr, endadr, labezsuf) ";
        $cmd .= "values ($res2[0], $res2[1], $res2[2], $res2[3], $res2[4], $res2[5], $res2[6], ";
        $cmd .= "'$res2[7]', '$lesart', $res2[9], $res2[10], '$res2[11]'); ";
        #print "$cmd\n";
        $dbh->do($cmd);
    }

}

# LocStemEd
$cmd = "INSERT INTO $target1 (varid, begadr, endadr) 
			SELECT DISTINCT labez, anfadr, endadr 
			FROM $source;";
#print $cmd."\n";
$dbh->do ($cmd);
# Update varnew
$cmd = "UPDATE $target1 SET varnew = varid;";
#print $cmd."\n";
$dbh->do ($cmd);
# Update s1 in LocStemEd
$cmd = "UPDATE $target1 SET s1 = '*' WHERE varid = 'a';";
#print $cmd."\n";
$dbh->do ($cmd);
$cmd = "UPDATE $target1 SET s1 = 'a' WHERE varid <> 'a';";
#print $cmd."\n";
$dbh->do ($cmd);
# Update s1 in VarGenAtt_ActNN
$cmd = "UPDATE $target3 SET varnew = varid;";
#print $cmd."\n";
$dbh->do ($cmd);
$cmd = "UPDATE $target3 SET s1 = '*' WHERE varid = 'a';";
#print $cmd."\n";
$dbh->do ($cmd);
$cmd = "UPDATE $target3 SET s1 = 'a' WHERE varid <> 'a';";
#print $cmd."\n";
$dbh->do ($cmd);

$dbh->disconnect ();
exit (0);
